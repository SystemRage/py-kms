#!/usr/bin/env python

# Copyright (c) 2003-2016 CORE Security Technologies
#
# This software is provided under under a slightly modified version
# of the Apache Software License. See the accompanying LICENSE file
# for more information.
#
# Description:
#   Partial C706.pdf + [MS-RPCE] implementation
#
#   Best way to learn how to use these calls is to grab the protocol standard
#   so you understand what the call does, and then read the test case located
#   at https://github.com/CoreSecurity/impacket/tree/master/impacket/testcases/SMB_RPC
#
# ToDo: 
# [ ] Take out all the security provider stuff out of here (e.g. RPC_C_AUTHN_WINNT)
#     and put it elsewhere. This will make the coder cleaner and easier to add 
#     more SSP (e.g. NETLOGON)
# 

"""
Stripped down version of: https://github.com/SecureAuthCorp/impacket/blob/master/impacket/dcerpc/v5/rpcrt.py
"""

from structure import Structure

# MS/RPC Constants
MSRPC_REQUEST   = 0x00
MSRPC_PING      = 0x01
MSRPC_RESPONSE  = 0x02
MSRPC_FAULT     = 0x03
MSRPC_WORKING   = 0x04
MSRPC_NOCALL    = 0x05
MSRPC_REJECT    = 0x06
MSRPC_ACK       = 0x07
MSRPC_CL_CANCEL = 0x08
MSRPC_FACK      = 0x09
MSRPC_CANCELACK = 0x0A
MSRPC_BIND      = 0x0B
MSRPC_BINDACK   = 0x0C
MSRPC_BINDNAK   = 0x0D
MSRPC_ALTERCTX  = 0x0E
MSRPC_ALTERCTX_R= 0x0F
MSRPC_AUTH3     = 0x10
MSRPC_SHUTDOWN  = 0x11
MSRPC_CO_CANCEL = 0x12
MSRPC_ORPHANED  = 0x13

# MS/RPC Packet Flags
PFC_FIRST_FRAG     = 0x01
PFC_LAST_FRAG      = 0x02

# For PDU types bind, bind_ack, alter_context, and
# alter_context_resp, this flag MUST be interpreted as PFC_SUPPORT_HEADER_SIGN
MSRPC_SUPPORT_SIGN  = 0x04

#For the
#remaining PDU types, this flag MUST be interpreted as PFC_PENDING_CANCEL.
MSRPC_PENDING_CANCEL= 0x04

PFC_RESERVED_1      = 0x08
PFC_CONC_MPX        = 0x10
PFC_DID_NOT_EXECUTE = 0x20
PFC_MAYBE           = 0x40
PFC_OBJECT_UUID     = 0x80

# Auth Types - Security Providers
RPC_C_AUTHN_NONE          = 0x00
RPC_C_AUTHN_GSS_NEGOTIATE = 0x09
RPC_C_AUTHN_WINNT         = 0x0A
RPC_C_AUTHN_GSS_SCHANNEL  = 0x0E
RPC_C_AUTHN_GSS_KERBEROS  = 0x10
RPC_C_AUTHN_NETLOGON      = 0x44
RPC_C_AUTHN_DEFAULT       = 0xFF

# Auth Levels
RPC_C_AUTHN_LEVEL_NONE          = 1
RPC_C_AUTHN_LEVEL_CONNECT       = 2
RPC_C_AUTHN_LEVEL_CALL          = 3
RPC_C_AUTHN_LEVEL_PKT           = 4
RPC_C_AUTHN_LEVEL_PKT_INTEGRITY = 5
RPC_C_AUTHN_LEVEL_PKT_PRIVACY   = 6

#Reasons for rejection of a context element, included in bind_ack result reason
rpc_provider_reason = {
    0       : 'reason_not_specified',
    1       : 'abstract_syntax_not_supported',
    2       : 'proposed_transfer_syntaxes_not_supported',
    3       : 'local_limit_exceeded',
    4       : 'protocol_version_not_specified',
    8       : 'authentication_type_not_recognized',
    9       : 'invalid_checksum'
}

MSRPC_CONT_RESULT_ACCEPT = 0
MSRPC_CONT_RESULT_USER_REJECT = 1
MSRPC_CONT_RESULT_PROV_REJECT = 2

#Results of a presentation context negotiation
rpc_cont_def_result = {
    0       : 'acceptance',
    1       : 'user_rejection',
    2       : 'provider_rejection'
}

#status codes, references:
#http://msdn.microsoft.com/library/default.asp?url=/library/en-us/rpc/rpc/rpc_return_values.asp
#http://msdn.microsoft.com/library/default.asp?url=/library/en-us/randz/protocol/common_return_values.asp
#winerror.h
#http://www.opengroup.org/onlinepubs/9629399/apdxn.htm

rpc_status_codes = {
    0x00000005L : 'rpc_s_access_denied',
    0x00000008L : 'Authentication type not recognized',
    0x000006D8L : 'rpc_fault_cant_perform', 
    0x000006C6L : 'rpc_x_invalid_bound',                # the arrays bound are invalid
    0x000006E4L : 'rpc_s_cannot_support: The requested operation is not supported.',               # some operation is not supported
    0x000006F7L : 'rpc_x_bad_stub_data',                # the stub data is invalid, doesn't match with the IDL definition
    0x1C010001L : 'nca_s_comm_failure',                 # unable to get response from server:
    0x1C010002L : 'nca_s_op_rng_error',                 # bad operation number in call
    0x1C010003L : 'nca_s_unk_if',                       # unknown interface
    0x1C010006L : 'nca_s_wrong_boot_time',              # client passed server wrong server boot time
    0x1C010009L : 'nca_s_you_crashed',                  # a restarted server called back a client
    0x1C01000BL : 'nca_s_proto_error',                  # someone messed up the protocol
    0x1C010013L : 'nca_s_out_args_too_big ',            # output args too big
    0x1C010014L : 'nca_s_server_too_busy',              # server is too busy to handle call
    0x1C010015L : 'nca_s_fault_string_too_long',        # string argument longer than declared max len
    0x1C010017L : 'nca_s_unsupported_type ',            # no implementation of generic operation for object
    0x1C000001L : 'nca_s_fault_int_div_by_zero',
    0x1C000002L : 'nca_s_fault_addr_error ',
    0x1C000003L : 'nca_s_fault_fp_div_zero',
    0x1C000004L : 'nca_s_fault_fp_underflow',
    0x1C000005L : 'nca_s_fault_fp_overflow',
    0x1C000006L : 'nca_s_fault_invalid_tag',
    0x1C000007L : 'nca_s_fault_invalid_bound ',
    0x1C000008L : 'nca_s_rpc_version_mismatch',
    0x1C000009L : 'nca_s_unspec_reject ',
    0x1C00000AL : 'nca_s_bad_actid',
    0x1C00000BL : 'nca_s_who_are_you_failed',
    0x1C00000CL : 'nca_s_manager_not_entered ',
    0x1C00000DL : 'nca_s_fault_cancel',
    0x1C00000EL : 'nca_s_fault_ill_inst',
    0x1C00000FL : 'nca_s_fault_fp_error',
    0x1C000010L : 'nca_s_fault_int_overflow',
    0x1C000012L : 'nca_s_fault_unspec',
    0x1C000013L : 'nca_s_fault_remote_comm_failure ',
    0x1C000014L : 'nca_s_fault_pipe_empty ',
    0x1C000015L : 'nca_s_fault_pipe_closed',
    0x1C000016L : 'nca_s_fault_pipe_order ',
    0x1C000017L : 'nca_s_fault_pipe_discipline',
    0x1C000018L : 'nca_s_fault_pipe_comm_error',
    0x1C000019L : 'nca_s_fault_pipe_memory',
    0x1C00001AL : 'nca_s_fault_context_mismatch ',
    0x1C00001BL : 'nca_s_fault_remote_no_memory ',
    0x1C00001CL : 'nca_s_invalid_pres_context_id',
    0x1C00001DL : 'nca_s_unsupported_authn_level',
    0x1C00001FL : 'nca_s_invalid_checksum ',
    0x1C000020L : 'nca_s_invalid_crc',
    0x1C000021L : 'nca_s_fault_user_defined',
    0x1C000022L : 'nca_s_fault_tx_open_failed',
    0x1C000023L : 'nca_s_fault_codeset_conv_error',
    0x1C000024L : 'nca_s_fault_object_not_found ',
    0x1C000025L : 'nca_s_fault_no_client_stub',
    0x16c9a000L : "rpc_s_mod",
    0x16c9a001L : "rpc_s_op_rng_error",
    0x16c9a002L : "rpc_s_cant_create_socket",
    0x16c9a003L : "rpc_s_cant_bind_socket",
    0x16c9a004L : "rpc_s_not_in_call",
    0x16c9a005L : "rpc_s_no_port",
    0x16c9a006L : "rpc_s_wrong_boot_time",
    0x16c9a007L : "rpc_s_too_many_sockets",
    0x16c9a008L : "rpc_s_illegal_register",
    0x16c9a009L : "rpc_s_cant_recv",
    0x16c9a00aL : "rpc_s_bad_pkt",
    0x16c9a00bL : "rpc_s_unbound_handle",
    0x16c9a00cL : "rpc_s_addr_in_use",
    0x16c9a00dL : "rpc_s_in_args_too_big",
    0x16c9a00eL : "rpc_s_string_too_long",
    0x16c9a00fL : "rpc_s_too_many_objects",
    0x16c9a010L : "rpc_s_binding_has_no_auth",
    0x16c9a011L : "rpc_s_unknown_authn_service",
    0x16c9a012L : "rpc_s_no_memory",
    0x16c9a013L : "rpc_s_cant_nmalloc",
    0x16c9a014L : "rpc_s_call_faulted",
    0x16c9a015L : "rpc_s_call_failed",
    0x16c9a016L : "rpc_s_comm_failure",
    0x16c9a017L : "rpc_s_rpcd_comm_failure",
    0x16c9a018L : "rpc_s_illegal_family_rebind",
    0x16c9a019L : "rpc_s_invalid_handle",
    0x16c9a01aL : "rpc_s_coding_error",
    0x16c9a01bL : "rpc_s_object_not_found",
    0x16c9a01cL : "rpc_s_cthread_not_found",
    0x16c9a01dL : "rpc_s_invalid_binding",
    0x16c9a01eL : "rpc_s_already_registered",
    0x16c9a01fL : "rpc_s_endpoint_not_found",
    0x16c9a020L : "rpc_s_invalid_rpc_protseq",
    0x16c9a021L : "rpc_s_desc_not_registered",
    0x16c9a022L : "rpc_s_already_listening",
    0x16c9a023L : "rpc_s_no_protseqs",
    0x16c9a024L : "rpc_s_no_protseqs_registered",
    0x16c9a025L : "rpc_s_no_bindings",
    0x16c9a026L : "rpc_s_max_descs_exceeded",
    0x16c9a027L : "rpc_s_no_interfaces",
    0x16c9a028L : "rpc_s_invalid_timeout",
    0x16c9a029L : "rpc_s_cant_inq_socket",
    0x16c9a02aL : "rpc_s_invalid_naf_id",
    0x16c9a02bL : "rpc_s_inval_net_addr",
    0x16c9a02cL : "rpc_s_unknown_if",
    0x16c9a02dL : "rpc_s_unsupported_type",
    0x16c9a02eL : "rpc_s_invalid_call_opt",
    0x16c9a02fL : "rpc_s_no_fault",
    0x16c9a030L : "rpc_s_cancel_timeout",
    0x16c9a031L : "rpc_s_call_cancelled",
    0x16c9a032L : "rpc_s_invalid_call_handle",
    0x16c9a033L : "rpc_s_cannot_alloc_assoc",
    0x16c9a034L : "rpc_s_cannot_connect",
    0x16c9a035L : "rpc_s_connection_aborted",
    0x16c9a036L : "rpc_s_connection_closed",
    0x16c9a037L : "rpc_s_cannot_accept",
    0x16c9a038L : "rpc_s_assoc_grp_not_found",
    0x16c9a039L : "rpc_s_stub_interface_error",
    0x16c9a03aL : "rpc_s_invalid_object",
    0x16c9a03bL : "rpc_s_invalid_type",
    0x16c9a03cL : "rpc_s_invalid_if_opnum",
    0x16c9a03dL : "rpc_s_different_server_instance",
    0x16c9a03eL : "rpc_s_protocol_error",
    0x16c9a03fL : "rpc_s_cant_recvmsg",
    0x16c9a040L : "rpc_s_invalid_string_binding",
    0x16c9a041L : "rpc_s_connect_timed_out",
    0x16c9a042L : "rpc_s_connect_rejected",
    0x16c9a043L : "rpc_s_network_unreachable",
    0x16c9a044L : "rpc_s_connect_no_resources",
    0x16c9a045L : "rpc_s_rem_network_shutdown",
    0x16c9a046L : "rpc_s_too_many_rem_connects",
    0x16c9a047L : "rpc_s_no_rem_endpoint",
    0x16c9a048L : "rpc_s_rem_host_down",
    0x16c9a049L : "rpc_s_host_unreachable",
    0x16c9a04aL : "rpc_s_access_control_info_inv",
    0x16c9a04bL : "rpc_s_loc_connect_aborted",
    0x16c9a04cL : "rpc_s_connect_closed_by_rem",
    0x16c9a04dL : "rpc_s_rem_host_crashed",
    0x16c9a04eL : "rpc_s_invalid_endpoint_format",
    0x16c9a04fL : "rpc_s_unknown_status_code",
    0x16c9a050L : "rpc_s_unknown_mgr_type",
    0x16c9a051L : "rpc_s_assoc_creation_failed",
    0x16c9a052L : "rpc_s_assoc_grp_max_exceeded",
    0x16c9a053L : "rpc_s_assoc_grp_alloc_failed",
    0x16c9a054L : "rpc_s_sm_invalid_state",
    0x16c9a055L : "rpc_s_assoc_req_rejected",
    0x16c9a056L : "rpc_s_assoc_shutdown",
    0x16c9a057L : "rpc_s_tsyntaxes_unsupported",
    0x16c9a058L : "rpc_s_context_id_not_found",
    0x16c9a059L : "rpc_s_cant_listen_socket",
    0x16c9a05aL : "rpc_s_no_addrs",
    0x16c9a05bL : "rpc_s_cant_getpeername",
    0x16c9a05cL : "rpc_s_cant_get_if_id",
    0x16c9a05dL : "rpc_s_protseq_not_supported",
    0x16c9a05eL : "rpc_s_call_orphaned",
    0x16c9a05fL : "rpc_s_who_are_you_failed",
    0x16c9a060L : "rpc_s_unknown_reject",
    0x16c9a061L : "rpc_s_type_already_registered",
    0x16c9a062L : "rpc_s_stop_listening_disabled",
    0x16c9a063L : "rpc_s_invalid_arg",
    0x16c9a064L : "rpc_s_not_supported",
    0x16c9a065L : "rpc_s_wrong_kind_of_binding",
    0x16c9a066L : "rpc_s_authn_authz_mismatch",
    0x16c9a067L : "rpc_s_call_queued",
    0x16c9a068L : "rpc_s_cannot_set_nodelay",
    0x16c9a069L : "rpc_s_not_rpc_tower",
    0x16c9a06aL : "rpc_s_invalid_rpc_protid",
    0x16c9a06bL : "rpc_s_invalid_rpc_floor",
    0x16c9a06cL : "rpc_s_call_timeout",
    0x16c9a06dL : "rpc_s_mgmt_op_disallowed",
    0x16c9a06eL : "rpc_s_manager_not_entered",
    0x16c9a06fL : "rpc_s_calls_too_large_for_wk_ep",
    0x16c9a070L : "rpc_s_server_too_busy",
    0x16c9a071L : "rpc_s_prot_version_mismatch",
    0x16c9a072L : "rpc_s_rpc_prot_version_mismatch",
    0x16c9a073L : "rpc_s_ss_no_import_cursor",
    0x16c9a074L : "rpc_s_fault_addr_error",
    0x16c9a075L : "rpc_s_fault_context_mismatch",
    0x16c9a076L : "rpc_s_fault_fp_div_by_zero",
    0x16c9a077L : "rpc_s_fault_fp_error",
    0x16c9a078L : "rpc_s_fault_fp_overflow",
    0x16c9a079L : "rpc_s_fault_fp_underflow",
    0x16c9a07aL : "rpc_s_fault_ill_inst",
    0x16c9a07bL : "rpc_s_fault_int_div_by_zero",
    0x16c9a07cL : "rpc_s_fault_int_overflow",
    0x16c9a07dL : "rpc_s_fault_invalid_bound",
    0x16c9a07eL : "rpc_s_fault_invalid_tag",
    0x16c9a07fL : "rpc_s_fault_pipe_closed",
    0x16c9a080L : "rpc_s_fault_pipe_comm_error",
    0x16c9a081L : "rpc_s_fault_pipe_discipline",
    0x16c9a082L : "rpc_s_fault_pipe_empty",
    0x16c9a083L : "rpc_s_fault_pipe_memory",
    0x16c9a084L : "rpc_s_fault_pipe_order",
    0x16c9a085L : "rpc_s_fault_remote_comm_failure",
    0x16c9a086L : "rpc_s_fault_remote_no_memory",
    0x16c9a087L : "rpc_s_fault_unspec",
    0x16c9a088L : "uuid_s_bad_version",
    0x16c9a089L : "uuid_s_socket_failure",
    0x16c9a08aL : "uuid_s_getconf_failure",
    0x16c9a08bL : "uuid_s_no_address",
    0x16c9a08cL : "uuid_s_overrun",
    0x16c9a08dL : "uuid_s_internal_error",
    0x16c9a08eL : "uuid_s_coding_error",
    0x16c9a08fL : "uuid_s_invalid_string_uuid",
    0x16c9a090L : "uuid_s_no_memory",
    0x16c9a091L : "rpc_s_no_more_entries",
    0x16c9a092L : "rpc_s_unknown_ns_error",
    0x16c9a093L : "rpc_s_name_service_unavailable",
    0x16c9a094L : "rpc_s_incomplete_name",
    0x16c9a095L : "rpc_s_group_not_found",
    0x16c9a096L : "rpc_s_invalid_name_syntax",
    0x16c9a097L : "rpc_s_no_more_members",
    0x16c9a098L : "rpc_s_no_more_interfaces",
    0x16c9a099L : "rpc_s_invalid_name_service",
    0x16c9a09aL : "rpc_s_no_name_mapping",
    0x16c9a09bL : "rpc_s_profile_not_found",
    0x16c9a09cL : "rpc_s_not_found",
    0x16c9a09dL : "rpc_s_no_updates",
    0x16c9a09eL : "rpc_s_update_failed",
    0x16c9a09fL : "rpc_s_no_match_exported",
    0x16c9a0a0L : "rpc_s_entry_not_found",
    0x16c9a0a1L : "rpc_s_invalid_inquiry_context",
    0x16c9a0a2L : "rpc_s_interface_not_found",
    0x16c9a0a3L : "rpc_s_group_member_not_found",
    0x16c9a0a4L : "rpc_s_entry_already_exists",
    0x16c9a0a5L : "rpc_s_nsinit_failure",
    0x16c9a0a6L : "rpc_s_unsupported_name_syntax",
    0x16c9a0a7L : "rpc_s_no_more_elements",
    0x16c9a0a8L : "rpc_s_no_ns_permission",
    0x16c9a0a9L : "rpc_s_invalid_inquiry_type",
    0x16c9a0aaL : "rpc_s_profile_element_not_found",
    0x16c9a0abL : "rpc_s_profile_element_replaced",
    0x16c9a0acL : "rpc_s_import_already_done",
    0x16c9a0adL : "rpc_s_database_busy",
    0x16c9a0aeL : "rpc_s_invalid_import_context",
    0x16c9a0afL : "rpc_s_uuid_set_not_found",
    0x16c9a0b0L : "rpc_s_uuid_member_not_found",
    0x16c9a0b1L : "rpc_s_no_interfaces_exported",
    0x16c9a0b2L : "rpc_s_tower_set_not_found",
    0x16c9a0b3L : "rpc_s_tower_member_not_found",
    0x16c9a0b4L : "rpc_s_obj_uuid_not_found",
    0x16c9a0b5L : "rpc_s_no_more_bindings",
    0x16c9a0b6L : "rpc_s_invalid_priority",
    0x16c9a0b7L : "rpc_s_not_rpc_entry",
    0x16c9a0b8L : "rpc_s_invalid_lookup_context",
    0x16c9a0b9L : "rpc_s_binding_vector_full",
    0x16c9a0baL : "rpc_s_cycle_detected",
    0x16c9a0bbL : "rpc_s_nothing_to_export",
    0x16c9a0bcL : "rpc_s_nothing_to_unexport",
    0x16c9a0bdL : "rpc_s_invalid_vers_option",
    0x16c9a0beL : "rpc_s_no_rpc_data",
    0x16c9a0bfL : "rpc_s_mbr_picked",
    0x16c9a0c0L : "rpc_s_not_all_objs_unexported",
    0x16c9a0c1L : "rpc_s_no_entry_name",
    0x16c9a0c2L : "rpc_s_priority_group_done",
    0x16c9a0c3L : "rpc_s_partial_results",
    0x16c9a0c4L : "rpc_s_no_env_setup",
    0x16c9a0c5L : "twr_s_unknown_sa",
    0x16c9a0c6L : "twr_s_unknown_tower",
    0x16c9a0c7L : "twr_s_not_implemented",
    0x16c9a0c8L : "rpc_s_max_calls_too_small",
    0x16c9a0c9L : "rpc_s_cthread_create_failed",
    0x16c9a0caL : "rpc_s_cthread_pool_exists",
    0x16c9a0cbL : "rpc_s_cthread_no_such_pool",
    0x16c9a0ccL : "rpc_s_cthread_invoke_disabled",
    0x16c9a0cdL : "ept_s_cant_perform_op",
    0x16c9a0ceL : "ept_s_no_memory",
    0x16c9a0cfL : "ept_s_database_invalid",
    0x16c9a0d0L : "ept_s_cant_create",
    0x16c9a0d1L : "ept_s_cant_access",
    0x16c9a0d2L : "ept_s_database_already_open",
    0x16c9a0d3L : "ept_s_invalid_entry",
    0x16c9a0d4L : "ept_s_update_failed",
    0x16c9a0d5L : "ept_s_invalid_context",
    0x16c9a0d6L : "ept_s_not_registered",
    0x16c9a0d7L : "ept_s_server_unavailable",
    0x16c9a0d8L : "rpc_s_underspecified_name",
    0x16c9a0d9L : "rpc_s_invalid_ns_handle",
    0x16c9a0daL : "rpc_s_unknown_error",
    0x16c9a0dbL : "rpc_s_ss_char_trans_open_fail",
    0x16c9a0dcL : "rpc_s_ss_char_trans_short_file",
    0x16c9a0ddL : "rpc_s_ss_context_damaged",
    0x16c9a0deL : "rpc_s_ss_in_null_context",
    0x16c9a0dfL : "rpc_s_socket_failure",
    0x16c9a0e0L : "rpc_s_unsupported_protect_level",
    0x16c9a0e1L : "rpc_s_invalid_checksum",
    0x16c9a0e2L : "rpc_s_invalid_credentials",
    0x16c9a0e3L : "rpc_s_credentials_too_large",
    0x16c9a0e4L : "rpc_s_call_id_not_found",
    0x16c9a0e5L : "rpc_s_key_id_not_found",
    0x16c9a0e6L : "rpc_s_auth_bad_integrity",
    0x16c9a0e7L : "rpc_s_auth_tkt_expired",
    0x16c9a0e8L : "rpc_s_auth_tkt_nyv",
    0x16c9a0e9L : "rpc_s_auth_repeat",
    0x16c9a0eaL : "rpc_s_auth_not_us",
    0x16c9a0ebL : "rpc_s_auth_badmatch",
    0x16c9a0ecL : "rpc_s_auth_skew",
    0x16c9a0edL : "rpc_s_auth_badaddr",
    0x16c9a0eeL : "rpc_s_auth_badversion",
    0x16c9a0efL : "rpc_s_auth_msg_type",
    0x16c9a0f0L : "rpc_s_auth_modified",
    0x16c9a0f1L : "rpc_s_auth_badorder",
    0x16c9a0f2L : "rpc_s_auth_badkeyver",
    0x16c9a0f3L : "rpc_s_auth_nokey",
    0x16c9a0f4L : "rpc_s_auth_mut_fail",
    0x16c9a0f5L : "rpc_s_auth_baddirection",
    0x16c9a0f6L : "rpc_s_auth_method",
    0x16c9a0f7L : "rpc_s_auth_badseq",
    0x16c9a0f8L : "rpc_s_auth_inapp_cksum",
    0x16c9a0f9L : "rpc_s_auth_field_toolong",
    0x16c9a0faL : "rpc_s_invalid_crc",
    0x16c9a0fbL : "rpc_s_binding_incomplete",
    0x16c9a0fcL : "rpc_s_key_func_not_allowed",
    0x16c9a0fdL : "rpc_s_unknown_stub_rtl_if_vers",
    0x16c9a0feL : "rpc_s_unknown_ifspec_vers",
    0x16c9a0ffL : "rpc_s_proto_unsupp_by_auth",
    0x16c9a100L : "rpc_s_authn_challenge_malformed",
    0x16c9a101L : "rpc_s_protect_level_mismatch",
    0x16c9a102L : "rpc_s_no_mepv",
    0x16c9a103L : "rpc_s_stub_protocol_error",
    0x16c9a104L : "rpc_s_class_version_mismatch",
    0x16c9a105L : "rpc_s_helper_not_running",
    0x16c9a106L : "rpc_s_helper_short_read",
    0x16c9a107L : "rpc_s_helper_catatonic",
    0x16c9a108L : "rpc_s_helper_aborted",
    0x16c9a109L : "rpc_s_not_in_kernel",
    0x16c9a10aL : "rpc_s_helper_wrong_user",
    0x16c9a10bL : "rpc_s_helper_overflow",
    0x16c9a10cL : "rpc_s_dg_need_way_auth",
    0x16c9a10dL : "rpc_s_unsupported_auth_subtype",
    0x16c9a10eL : "rpc_s_wrong_pickle_type",
    0x16c9a10fL : "rpc_s_not_listening",
    0x16c9a110L : "rpc_s_ss_bad_buffer",
    0x16c9a111L : "rpc_s_ss_bad_es_action",
    0x16c9a112L : "rpc_s_ss_wrong_es_version",
    0x16c9a113L : "rpc_s_fault_user_defined",
    0x16c9a114L : "rpc_s_ss_incompatible_codesets",
    0x16c9a115L : "rpc_s_tx_not_in_transaction",
    0x16c9a116L : "rpc_s_tx_open_failed",
    0x16c9a117L : "rpc_s_partial_credentials",
    0x16c9a118L : "rpc_s_ss_invalid_codeset_tag",
    0x16c9a119L : "rpc_s_mgmt_bad_type",
    0x16c9a11aL : "rpc_s_ss_invalid_char_input",
    0x16c9a11bL : "rpc_s_ss_short_conv_buffer",
    0x16c9a11cL : "rpc_s_ss_iconv_error",
    0x16c9a11dL : "rpc_s_ss_no_compat_codeset",
    0x16c9a11eL : "rpc_s_ss_no_compat_charsets",
    0x16c9a11fL : "dce_cs_c_ok",
    0x16c9a120L : "dce_cs_c_unknown",
    0x16c9a121L : "dce_cs_c_notfound",
    0x16c9a122L : "dce_cs_c_cannot_open_file",
    0x16c9a123L : "dce_cs_c_cannot_read_file",
    0x16c9a124L : "dce_cs_c_cannot_allocate_memory",
    0x16c9a125L : "rpc_s_ss_cleanup_failed",
    0x16c9a126L : "rpc_svc_desc_general",
    0x16c9a127L : "rpc_svc_desc_mutex",
    0x16c9a128L : "rpc_svc_desc_xmit",
    0x16c9a129L : "rpc_svc_desc_recv",
    0x16c9a12aL : "rpc_svc_desc_dg_state",
    0x16c9a12bL : "rpc_svc_desc_cancel",
    0x16c9a12cL : "rpc_svc_desc_orphan",
    0x16c9a12dL : "rpc_svc_desc_cn_state",
    0x16c9a12eL : "rpc_svc_desc_cn_pkt",
    0x16c9a12fL : "rpc_svc_desc_pkt_quotas",
    0x16c9a130L : "rpc_svc_desc_auth",
    0x16c9a131L : "rpc_svc_desc_source",
    0x16c9a132L : "rpc_svc_desc_stats",
    0x16c9a133L : "rpc_svc_desc_mem",
    0x16c9a134L : "rpc_svc_desc_mem_type",
    0x16c9a135L : "rpc_svc_desc_dg_pktlog",
    0x16c9a136L : "rpc_svc_desc_thread_id",
    0x16c9a137L : "rpc_svc_desc_timestamp",
    0x16c9a138L : "rpc_svc_desc_cn_errors",
    0x16c9a139L : "rpc_svc_desc_conv_thread",
    0x16c9a13aL : "rpc_svc_desc_pid",
    0x16c9a13bL : "rpc_svc_desc_atfork",
    0x16c9a13cL : "rpc_svc_desc_cma_thread",
    0x16c9a13dL : "rpc_svc_desc_inherit",
    0x16c9a13eL : "rpc_svc_desc_dg_sockets",
    0x16c9a13fL : "rpc_svc_desc_timer",
    0x16c9a140L : "rpc_svc_desc_threads",
    0x16c9a141L : "rpc_svc_desc_server_call",
    0x16c9a142L : "rpc_svc_desc_nsi",
    0x16c9a143L : "rpc_svc_desc_dg_pkt",
    0x16c9a144L : "rpc_m_cn_ill_state_trans_sa",
    0x16c9a145L : "rpc_m_cn_ill_state_trans_ca",
    0x16c9a146L : "rpc_m_cn_ill_state_trans_sg",
    0x16c9a147L : "rpc_m_cn_ill_state_trans_cg",
    0x16c9a148L : "rpc_m_cn_ill_state_trans_sr",
    0x16c9a149L : "rpc_m_cn_ill_state_trans_cr",
    0x16c9a14aL : "rpc_m_bad_pkt_type",
    0x16c9a14bL : "rpc_m_prot_mismatch",
    0x16c9a14cL : "rpc_m_frag_toobig",
    0x16c9a14dL : "rpc_m_unsupp_stub_rtl_if",
    0x16c9a14eL : "rpc_m_unhandled_callstate",
    0x16c9a14fL : "rpc_m_call_failed",
    0x16c9a150L : "rpc_m_call_failed_no_status",
    0x16c9a151L : "rpc_m_call_failed_errno",
    0x16c9a152L : "rpc_m_call_failed_s",
    0x16c9a153L : "rpc_m_call_failed_c",
    0x16c9a154L : "rpc_m_errmsg_toobig",
    0x16c9a155L : "rpc_m_invalid_srchattr",
    0x16c9a156L : "rpc_m_nts_not_found",
    0x16c9a157L : "rpc_m_invalid_accbytcnt",
    0x16c9a158L : "rpc_m_pre_v2_ifspec",
    0x16c9a159L : "rpc_m_unk_ifspec",
    0x16c9a15aL : "rpc_m_recvbuf_toosmall",
    0x16c9a15bL : "rpc_m_unalign_authtrl",
    0x16c9a15cL : "rpc_m_unexpected_exc",
    0x16c9a15dL : "rpc_m_no_stub_data",
    0x16c9a15eL : "rpc_m_eventlist_full",
    0x16c9a15fL : "rpc_m_unk_sock_type",
    0x16c9a160L : "rpc_m_unimp_call",
    0x16c9a161L : "rpc_m_invalid_seqnum",
    0x16c9a162L : "rpc_m_cant_create_uuid",
    0x16c9a163L : "rpc_m_pre_v2_ss",
    0x16c9a164L : "rpc_m_dgpkt_pool_corrupt",
    0x16c9a165L : "rpc_m_dgpkt_bad_free",
    0x16c9a166L : "rpc_m_lookaside_corrupt",
    0x16c9a167L : "rpc_m_alloc_fail",
    0x16c9a168L : "rpc_m_realloc_fail",
    0x16c9a169L : "rpc_m_cant_open_file",
    0x16c9a16aL : "rpc_m_cant_read_addr",
    0x16c9a16bL : "rpc_svc_desc_libidl",
    0x16c9a16cL : "rpc_m_ctxrundown_nomem",
    0x16c9a16dL : "rpc_m_ctxrundown_exc",
    0x16c9a16eL : "rpc_s_fault_codeset_conv_error",
    0x16c9a16fL : "rpc_s_no_call_active",
    0x16c9a170L : "rpc_s_cannot_support",
    0x16c9a171L : "rpc_s_no_context_available",
}

# Context Item
class CtxItem(Structure):
    structure = (
        ('ContextID','<H=0'),
        ('TransItems','B=0'),
        ('Pad','B=0'),
        ('AbstractSyntax','20s=""'),
        ('TransferSyntax','20s=""'),
    )

class CtxItemResult(Structure):
    structure = (
        ('Result','<H=0'),
        ('Reason','<H=0'),
        ('TransferSyntax','20s=""'),
    )

class SEC_TRAILER(Structure):
    commonHdr = (
        ('auth_type', 'B=10'),
        ('auth_level','B=0'),
        ('auth_pad_len','B=0'),
        ('auth_rsvrd','B=0'),
        ('auth_ctx_id','<L=747920'),
    )

class MSRPCHeader(Structure):
    _SIZE = 16
    commonHdr = ( 
        ('ver_major','B=5'),                              # 0
        ('ver_minor','B=0'),                              # 1
        ('type','B=0'),                                   # 2
        ('flags','B=0'),                                  # 3
        ('representation','<L=0x10'),                     # 4
        ('frag_len','<H=self._SIZE+len(auth_data)+(16 if (self["flags"] & 0x80) > 0 else 0)+len(pduData)+len(pad)+len(sec_trailer)'),  # 8
        ('auth_len','<H=len(auth_data)'),                 # 10
        ('call_id','<L=1'),                               # 12    <-- Common up to here (including this)
    )

    structure = ( 
        ('dataLen','_-pduData','self["frag_len"]-self["auth_len"]-self._SIZE-(8 if self["auth_len"] > 0 else 0)'),
        ('pduData',':'),                                
        ('_pad', '_-pad','(4 - ((self._SIZE + (16 if (self["flags"] & 0x80) > 0 else 0) + len(self["pduData"])) & 3) & 3)'),
        ('pad', ':'),
        ('_sec_trailer', '_-sec_trailer', '8 if self["auth_len"] > 0 else 0'),
        ('sec_trailer',':'),
        ('auth_dataLen','_-auth_data','self["auth_len"]'),
        ('auth_data',':'),
    )

    def __init__(self, data = None, alignment = 0):
        Structure.__init__(self,data, alignment)
        if data is None:
            self['ver_major'] = 5
            self['ver_minor'] = 0
            self['flags'] = PFC_FIRST_FRAG | PFC_LAST_FRAG
            self['type'] = MSRPC_REQUEST
            self.__frag_len_set = 0
            self['auth_len'] = 0
            self['pduData'] = ''
            self['auth_data'] = ''
            self['sec_trailer'] = ''
            self['pad'] = ''

    def get_header_size(self):
        return self._SIZE + (16 if (self["flags"] & PFC_OBJECT_UUID) > 0 else 0)

    def get_packet(self):
        if self['auth_data'] != '':
            self['auth_len'] = len(self['auth_data'])
        # The sec_trailer structure MUST be 4-byte aligned with respect to 
        # the beginning of the PDU. Padding octets MUST be used to align the 
        # sec_trailer structure if its natural beginning is not already 4-byte aligned
        ##self['pad'] = '\xAA' * (4 - ((self._SIZE + len(self['pduData'])) & 3) & 3)

        return self.getData()

class MSRPCRequestHeader(MSRPCHeader):
    _SIZE = 24
    commonHdr = MSRPCHeader.commonHdr + ( 
        ('alloc_hint','<L=0'),                            # 16
        ('ctx_id','<H=0'),                                # 20
        ('op_num','<H=0'),                                # 22
        ('_uuid','_-uuid','16 if self["flags"] & 0x80 > 0 else 0' ), # 22
        ('uuid',':'),                                # 22
    )

    def __init__(self, data = None, alignment = 0):
        MSRPCHeader.__init__(self, data, alignment)
        if data is None:
           self['type'] = MSRPC_REQUEST
           self['ctx_id'] = 0
           self['uuid'] = ''

class MSRPCRespHeader(MSRPCHeader):
    _SIZE = 24
    commonHdr = MSRPCHeader.commonHdr + ( 
        ('alloc_hint','<L=0'),                          # 16   
        ('ctx_id','<H=0'),                              # 20
        ('cancel_count','<B=0'),                        # 22
        ('padding','<B=0'),                             # 23
    )

    def __init__(self, aBuffer = None, alignment = 0):
        MSRPCHeader.__init__(self, aBuffer, alignment)
        if aBuffer is None:
            self['type'] = MSRPC_RESPONSE
            self['ctx_id'] = 0

class MSRPCBind(Structure):
    _CTX_ITEM_LEN = len(CtxItem())
    structure = ( 
        ('max_tfrag','<H=4280'),
        ('max_rfrag','<H=4280'),
        ('assoc_group','<L=0'),
        ('ctx_num','B=0'),
        ('Reserved','B=0'),
        ('Reserved2','<H=0'),
        ('_ctx_items', '_-ctx_items', 'self["ctx_num"]*self._CTX_ITEM_LEN'),
        ('ctx_items',':'),
    )
 
    def __init__(self, data = None, alignment = 0):
        Structure.__init__(self, data, alignment)
        if data is None:
            self['max_tfrag'] = 4280
            self['max_rfrag'] = 4280
            self['assoc_group'] = 0
            self['ctx_num'] = 1
            self['ctx_items'] = ''
        self.__ctx_items = []

    def addCtxItem(self, item):
        self.__ctx_items.append(item)
    
    def getData(self):
        self['ctx_num'] = len(self.__ctx_items)
        for i in self.__ctx_items:
            self['ctx_items'] += i.getData()
        return Structure.getData(self)

class MSRPCBindAck(MSRPCHeader):
    _SIZE = 26 # Up to SecondaryAddr
    _CTX_ITEM_LEN = len(CtxItemResult())
    structure = ( 
        ('max_tfrag','<H=0'),
        ('max_rfrag','<H=0'),
        ('assoc_group','<L=0'),
        ('SecondaryAddrLen','<H&SecondaryAddr'), 
        ('SecondaryAddr','z'),                          # Optional if SecondaryAddrLen == 0
        ('PadLen','_-Pad','(4-((self["SecondaryAddrLen"]+self._SIZE) % 4))%4'),
        ('Pad',':'),
        ('ctx_num','B=0'),
        ('Reserved','B=0'),
        ('Reserved2','<H=0'),
        ('_ctx_items','_-ctx_items','self["ctx_num"]*self._CTX_ITEM_LEN'),
        ('ctx_items',':'),
        ('_sec_trailer', '_-sec_trailer', '8 if self["auth_len"] > 0 else 0'),
        ('sec_trailer',':'),
        ('auth_dataLen','_-auth_data','self["auth_len"]'),
        ('auth_data',':'),
    )
    def __init__(self, data = None, alignment = 0):
        self.__ctx_items = []
        MSRPCHeader.__init__(self,data,alignment)
        if data is None:
            self['Pad'] = ''
            self['ctx_items'] = ''
            self['sec_trailer'] = ''
            self['auth_data'] = ''

    def getCtxItems(self):
        return self.__ctx_items

    def getCtxItem(self,index):
        return self.__ctx_items[index-1]

    def fromString(self, data):
        Structure.fromString(self,data)
        # Parse the ctx_items
        data = self['ctx_items']
        for i in range(self['ctx_num']):
            item = CtxItemResult(data)
            self.__ctx_items.append(item)
            data = data[len(item):]
            
class MSRPCBindNak(Structure):
    structure = ( 
        ('RejectedReason','<H=0'),
        ('SupportedVersions',':'),
    )
    def __init__(self, data = None, alignment = 0):
        Structure.__init__(self,data,alignment)
        if data is None:
            self['SupportedVersions'] = ''
