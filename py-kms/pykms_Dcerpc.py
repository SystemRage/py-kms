#!/usr/bin/env python3

# SECUREAUTH LABS. Copyright 2018 SecureAuth Corporation. All rights reserved.
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
#   at https://github.com/SecureAuthCorp/impacket/tree/master/tests/SMB_RPC
#
# ToDo: 
# [ ] Take out all the security provider stuff out of here (e.g. RPC_C_AUTHN_WINNT)
#     and put it elsewhere. This will make the coder cleaner and easier to add 
#     more SSP (e.g. NETLOGON)
# 
"""
Stripped down version of:
https://github.com/SecureAuthCorp/impacket/blob/master/impacket/dcerpc/v5/rpcrt.py
"""

from pykms_Structure import Structure

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
#https://docs.microsoft.com/windows/desktop/Rpc/rpc-return-values
#https://msdn.microsoft.com/library/default.asp?url=/library/en-us/randz/protocol/common_return_values.asp
#winerror.h
#https://www.opengroup.org/onlinepubs/9629399/apdxn.htm

rpc_status_codes = {
    0x00000005 : 'rpc_s_access_denied',
    0x00000008 : 'Authentication type not recognized',
    0x000006D8 : 'rpc_fault_cant_perform', 
    0x000006C6 : 'rpc_x_invalid_bound',                # the arrays bound are invalid
    0x000006E4 : 'rpc_s_cannot_support: The requested operation is not supported.',               # some operation is not supported
    0x000006F7 : 'rpc_x_bad_stub_data',                # the stub data is invalid, doesn't match with the IDL definition
    0x1C010001 : 'nca_s_comm_failure',                 # unable to get response from server:
    0x1C010002 : 'nca_s_op_rng_error',                 # bad operation number in call
    0x1C010003 : 'nca_s_unk_if',                       # unknown interface
    0x1C010006 : 'nca_s_wrong_boot_time',              # client passed server wrong server boot time
    0x1C010009 : 'nca_s_you_crashed',                  # a restarted server called back a client
    0x1C01000B : 'nca_s_proto_error',                  # someone messed up the protocol
    0x1C010013 : 'nca_s_out_args_too_big ',            # output args too big
    0x1C010014 : 'nca_s_server_too_busy',              # server is too busy to handle call
    0x1C010015 : 'nca_s_fault_string_too_long',        # string argument longer than declared max len
    0x1C010017 : 'nca_s_unsupported_type ',            # no implementation of generic operation for object
    0x1C000001 : 'nca_s_fault_int_div_by_zero',
    0x1C000002 : 'nca_s_fault_addr_error ',
    0x1C000003 : 'nca_s_fault_fp_div_zero',
    0x1C000004 : 'nca_s_fault_fp_underflow',
    0x1C000005 : 'nca_s_fault_fp_overflow',
    0x1C000006 : 'nca_s_fault_invalid_tag',
    0x1C000007 : 'nca_s_fault_invalid_bound ',
    0x1C000008 : 'nca_s_rpc_version_mismatch',
    0x1C000009 : 'nca_s_unspec_reject ',
    0x1C00000A : 'nca_s_bad_actid',
    0x1C00000B : 'nca_s_who_are_you_failed',
    0x1C00000C : 'nca_s_manager_not_entered ',
    0x1C00000D : 'nca_s_fault_cancel',
    0x1C00000E : 'nca_s_fault_ill_inst',
    0x1C00000F : 'nca_s_fault_fp_error',
    0x1C000010 : 'nca_s_fault_int_overflow',
    0x1C000012 : 'nca_s_fault_unspec',
    0x1C000013 : 'nca_s_fault_remote_comm_failure ',
    0x1C000014 : 'nca_s_fault_pipe_empty ',
    0x1C000015 : 'nca_s_fault_pipe_closed',
    0x1C000016 : 'nca_s_fault_pipe_order ',
    0x1C000017 : 'nca_s_fault_pipe_discipline',
    0x1C000018 : 'nca_s_fault_pipe_comm_error',
    0x1C000019 : 'nca_s_fault_pipe_memory',
    0x1C00001A : 'nca_s_fault_context_mismatch ',
    0x1C00001B : 'nca_s_fault_remote_no_memory ',
    0x1C00001C : 'nca_s_invalid_pres_context_id',
    0x1C00001D : 'nca_s_unsupported_authn_level',
    0x1C00001F : 'nca_s_invalid_checksum ',
    0x1C000020 : 'nca_s_invalid_crc',
    0x1C000021 : 'nca_s_fault_user_defined',
    0x1C000022 : 'nca_s_fault_tx_open_failed',
    0x1C000023 : 'nca_s_fault_codeset_conv_error',
    0x1C000024 : 'nca_s_fault_object_not_found ',
    0x1C000025 : 'nca_s_fault_no_client_stub',
    0x16c9a000 : "rpc_s_mod",
    0x16c9a001 : "rpc_s_op_rng_error",
    0x16c9a002 : "rpc_s_cant_create_socket",
    0x16c9a003 : "rpc_s_cant_bind_socket",
    0x16c9a004 : "rpc_s_not_in_call",
    0x16c9a005 : "rpc_s_no_port",
    0x16c9a006 : "rpc_s_wrong_boot_time",
    0x16c9a007 : "rpc_s_too_many_sockets",
    0x16c9a008 : "rpc_s_illegal_register",
    0x16c9a009 : "rpc_s_cant_recv",
    0x16c9a00a : "rpc_s_bad_pkt",
    0x16c9a00b : "rpc_s_unbound_handle",
    0x16c9a00c : "rpc_s_addr_in_use",
    0x16c9a00d : "rpc_s_in_args_too_big",
    0x16c9a00e : "rpc_s_string_too_long",
    0x16c9a00f : "rpc_s_too_many_objects",
    0x16c9a010 : "rpc_s_binding_has_no_auth",
    0x16c9a011 : "rpc_s_unknown_authn_service",
    0x16c9a012 : "rpc_s_no_memory",
    0x16c9a013 : "rpc_s_cant_nmalloc",
    0x16c9a014 : "rpc_s_call_faulted",
    0x16c9a015 : "rpc_s_call_failed",
    0x16c9a016 : "rpc_s_comm_failure",
    0x16c9a017 : "rpc_s_rpcd_comm_failure",
    0x16c9a018 : "rpc_s_illegal_family_rebind",
    0x16c9a019 : "rpc_s_invalid_handle",
    0x16c9a01a : "rpc_s_coding_error",
    0x16c9a01b : "rpc_s_object_not_found",
    0x16c9a01c : "rpc_s_cthread_not_found",
    0x16c9a01d : "rpc_s_invalid_binding",
    0x16c9a01e : "rpc_s_already_registered",
    0x16c9a01f : "rpc_s_endpoint_not_found",
    0x16c9a020 : "rpc_s_invalid_rpc_protseq",
    0x16c9a021 : "rpc_s_desc_not_registered",
    0x16c9a022 : "rpc_s_already_listening",
    0x16c9a023 : "rpc_s_no_protseqs",
    0x16c9a024 : "rpc_s_no_protseqs_registered",
    0x16c9a025 : "rpc_s_no_bindings",
    0x16c9a026 : "rpc_s_max_descs_exceeded",
    0x16c9a027 : "rpc_s_no_interfaces",
    0x16c9a028 : "rpc_s_invalid_timeout",
    0x16c9a029 : "rpc_s_cant_inq_socket",
    0x16c9a02a : "rpc_s_invalid_naf_id",
    0x16c9a02b : "rpc_s_inval_net_addr",
    0x16c9a02c : "rpc_s_unknown_if",
    0x16c9a02d : "rpc_s_unsupported_type",
    0x16c9a02e : "rpc_s_invalid_call_opt",
    0x16c9a02f : "rpc_s_no_fault",
    0x16c9a030 : "rpc_s_cancel_timeout",
    0x16c9a031 : "rpc_s_call_cancelled",
    0x16c9a032 : "rpc_s_invalid_call_handle",
    0x16c9a033 : "rpc_s_cannot_alloc_assoc",
    0x16c9a034 : "rpc_s_cannot_connect",
    0x16c9a035 : "rpc_s_connection_aborted",
    0x16c9a036 : "rpc_s_connection_closed",
    0x16c9a037 : "rpc_s_cannot_accept",
    0x16c9a038 : "rpc_s_assoc_grp_not_found",
    0x16c9a039 : "rpc_s_stub_interface_error",
    0x16c9a03a : "rpc_s_invalid_object",
    0x16c9a03b : "rpc_s_invalid_type",
    0x16c9a03c : "rpc_s_invalid_if_opnum",
    0x16c9a03d : "rpc_s_different_server_instance",
    0x16c9a03e : "rpc_s_protocol_error",
    0x16c9a03f : "rpc_s_cant_recvmsg",
    0x16c9a040 : "rpc_s_invalid_string_binding",
    0x16c9a041 : "rpc_s_connect_timed_out",
    0x16c9a042 : "rpc_s_connect_rejected",
    0x16c9a043 : "rpc_s_network_unreachable",
    0x16c9a044 : "rpc_s_connect_no_resources",
    0x16c9a045 : "rpc_s_rem_network_shutdown",
    0x16c9a046 : "rpc_s_too_many_rem_connects",
    0x16c9a047 : "rpc_s_no_rem_endpoint",
    0x16c9a048 : "rpc_s_rem_host_down",
    0x16c9a049 : "rpc_s_host_unreachable",
    0x16c9a04a : "rpc_s_access_control_info_inv",
    0x16c9a04b : "rpc_s_loc_connect_aborted",
    0x16c9a04c : "rpc_s_connect_closed_by_rem",
    0x16c9a04d : "rpc_s_rem_host_crashed",
    0x16c9a04e : "rpc_s_invalid_endpoint_format",
    0x16c9a04f : "rpc_s_unknown_status_code",
    0x16c9a050 : "rpc_s_unknown_mgr_type",
    0x16c9a051 : "rpc_s_assoc_creation_failed",
    0x16c9a052 : "rpc_s_assoc_grp_max_exceeded",
    0x16c9a053 : "rpc_s_assoc_grp_alloc_failed",
    0x16c9a054 : "rpc_s_sm_invalid_state",
    0x16c9a055 : "rpc_s_assoc_req_rejected",
    0x16c9a056 : "rpc_s_assoc_shutdown",
    0x16c9a057 : "rpc_s_tsyntaxes_unsupported",
    0x16c9a058 : "rpc_s_context_id_not_found",
    0x16c9a059 : "rpc_s_cant_listen_socket",
    0x16c9a05a : "rpc_s_no_addrs",
    0x16c9a05b : "rpc_s_cant_getpeername",
    0x16c9a05c : "rpc_s_cant_get_if_id",
    0x16c9a05d : "rpc_s_protseq_not_supported",
    0x16c9a05e : "rpc_s_call_orphaned",
    0x16c9a05f : "rpc_s_who_are_you_failed",
    0x16c9a060 : "rpc_s_unknown_reject",
    0x16c9a061 : "rpc_s_type_already_registered",
    0x16c9a062 : "rpc_s_stop_listening_disabled",
    0x16c9a063 : "rpc_s_invalid_arg",
    0x16c9a064 : "rpc_s_not_supported",
    0x16c9a065 : "rpc_s_wrong_kind_of_binding",
    0x16c9a066 : "rpc_s_authn_authz_mismatch",
    0x16c9a067 : "rpc_s_call_queued",
    0x16c9a068 : "rpc_s_cannot_set_nodelay",
    0x16c9a069 : "rpc_s_not_rpc_tower",
    0x16c9a06a : "rpc_s_invalid_rpc_protid",
    0x16c9a06b : "rpc_s_invalid_rpc_floor",
    0x16c9a06c : "rpc_s_call_timeout",
    0x16c9a06d : "rpc_s_mgmt_op_disallowed",
    0x16c9a06e : "rpc_s_manager_not_entered",
    0x16c9a06f : "rpc_s_calls_too_large_for_wk_ep",
    0x16c9a070 : "rpc_s_server_too_busy",
    0x16c9a071 : "rpc_s_prot_version_mismatch",
    0x16c9a072 : "rpc_s_rpc_prot_version_mismatch",
    0x16c9a073 : "rpc_s_ss_no_import_cursor",
    0x16c9a074 : "rpc_s_fault_addr_error",
    0x16c9a075 : "rpc_s_fault_context_mismatch",
    0x16c9a076 : "rpc_s_fault_fp_div_by_zero",
    0x16c9a077 : "rpc_s_fault_fp_error",
    0x16c9a078 : "rpc_s_fault_fp_overflow",
    0x16c9a079 : "rpc_s_fault_fp_underflow",
    0x16c9a07a : "rpc_s_fault_ill_inst",
    0x16c9a07b : "rpc_s_fault_int_div_by_zero",
    0x16c9a07c : "rpc_s_fault_int_overflow",
    0x16c9a07d : "rpc_s_fault_invalid_bound",
    0x16c9a07e : "rpc_s_fault_invalid_tag",
    0x16c9a07f : "rpc_s_fault_pipe_closed",
    0x16c9a080 : "rpc_s_fault_pipe_comm_error",
    0x16c9a081 : "rpc_s_fault_pipe_discipline",
    0x16c9a082 : "rpc_s_fault_pipe_empty",
    0x16c9a083 : "rpc_s_fault_pipe_memory",
    0x16c9a084 : "rpc_s_fault_pipe_order",
    0x16c9a085 : "rpc_s_fault_remote_comm_failure",
    0x16c9a086 : "rpc_s_fault_remote_no_memory",
    0x16c9a087 : "rpc_s_fault_unspec",
    0x16c9a088 : "uuid_s_bad_version",
    0x16c9a089 : "uuid_s_socket_failure",
    0x16c9a08a : "uuid_s_getconf_failure",
    0x16c9a08b : "uuid_s_no_address",
    0x16c9a08c : "uuid_s_overrun",
    0x16c9a08d : "uuid_s_internal_error",
    0x16c9a08e : "uuid_s_coding_error",
    0x16c9a08f : "uuid_s_invalid_string_uuid",
    0x16c9a090 : "uuid_s_no_memory",
    0x16c9a091 : "rpc_s_no_more_entries",
    0x16c9a092 : "rpc_s_unknown_ns_error",
    0x16c9a093 : "rpc_s_name_service_unavailable",
    0x16c9a094 : "rpc_s_incomplete_name",
    0x16c9a095 : "rpc_s_group_not_found",
    0x16c9a096 : "rpc_s_invalid_name_syntax",
    0x16c9a097 : "rpc_s_no_more_members",
    0x16c9a098 : "rpc_s_no_more_interfaces",
    0x16c9a099 : "rpc_s_invalid_name_service",
    0x16c9a09a : "rpc_s_no_name_mapping",
    0x16c9a09b : "rpc_s_profile_not_found",
    0x16c9a09c : "rpc_s_not_found",
    0x16c9a09d : "rpc_s_no_updates",
    0x16c9a09e : "rpc_s_update_failed",
    0x16c9a09f : "rpc_s_no_match_exported",
    0x16c9a0a0 : "rpc_s_entry_not_found",
    0x16c9a0a1 : "rpc_s_invalid_inquiry_context",
    0x16c9a0a2 : "rpc_s_interface_not_found",
    0x16c9a0a3 : "rpc_s_group_member_not_found",
    0x16c9a0a4 : "rpc_s_entry_already_exists",
    0x16c9a0a5 : "rpc_s_nsinit_failure",
    0x16c9a0a6 : "rpc_s_unsupported_name_syntax",
    0x16c9a0a7 : "rpc_s_no_more_elements",
    0x16c9a0a8 : "rpc_s_no_ns_permission",
    0x16c9a0a9 : "rpc_s_invalid_inquiry_type",
    0x16c9a0aa : "rpc_s_profile_element_not_found",
    0x16c9a0ab : "rpc_s_profile_element_replaced",
    0x16c9a0ac : "rpc_s_import_already_done",
    0x16c9a0ad : "rpc_s_database_busy",
    0x16c9a0ae : "rpc_s_invalid_import_context",
    0x16c9a0af : "rpc_s_uuid_set_not_found",
    0x16c9a0b0 : "rpc_s_uuid_member_not_found",
    0x16c9a0b1 : "rpc_s_no_interfaces_exported",
    0x16c9a0b2 : "rpc_s_tower_set_not_found",
    0x16c9a0b3 : "rpc_s_tower_member_not_found",
    0x16c9a0b4 : "rpc_s_obj_uuid_not_found",
    0x16c9a0b5 : "rpc_s_no_more_bindings",
    0x16c9a0b6 : "rpc_s_invalid_priority",
    0x16c9a0b7 : "rpc_s_not_rpc_entry",
    0x16c9a0b8 : "rpc_s_invalid_lookup_context",
    0x16c9a0b9 : "rpc_s_binding_vector_full",
    0x16c9a0ba : "rpc_s_cycle_detected",
    0x16c9a0bb : "rpc_s_nothing_to_export",
    0x16c9a0bc : "rpc_s_nothing_to_unexport",
    0x16c9a0bd : "rpc_s_invalid_vers_option",
    0x16c9a0be : "rpc_s_no_rpc_data",
    0x16c9a0bf : "rpc_s_mbr_picked",
    0x16c9a0c0 : "rpc_s_not_all_objs_unexported",
    0x16c9a0c1 : "rpc_s_no_entry_name",
    0x16c9a0c2 : "rpc_s_priority_group_done",
    0x16c9a0c3 : "rpc_s_partial_results",
    0x16c9a0c4 : "rpc_s_no_env_setup",
    0x16c9a0c5 : "twr_s_unknown_sa",
    0x16c9a0c6 : "twr_s_unknown_tower",
    0x16c9a0c7 : "twr_s_not_implemented",
    0x16c9a0c8 : "rpc_s_max_calls_too_small",
    0x16c9a0c9 : "rpc_s_cthread_create_failed",
    0x16c9a0ca : "rpc_s_cthread_pool_exists",
    0x16c9a0cb : "rpc_s_cthread_no_such_pool",
    0x16c9a0cc : "rpc_s_cthread_invoke_disabled",
    0x16c9a0cd : "ept_s_cant_perform_op",
    0x16c9a0ce : "ept_s_no_memory",
    0x16c9a0cf : "ept_s_database_invalid",
    0x16c9a0d0 : "ept_s_cant_create",
    0x16c9a0d1 : "ept_s_cant_access",
    0x16c9a0d2 : "ept_s_database_already_open",
    0x16c9a0d3 : "ept_s_invalid_entry",
    0x16c9a0d4 : "ept_s_update_failed",
    0x16c9a0d5 : "ept_s_invalid_context",
    0x16c9a0d6 : "ept_s_not_registered",
    0x16c9a0d7 : "ept_s_server_unavailable",
    0x16c9a0d8 : "rpc_s_underspecified_name",
    0x16c9a0d9 : "rpc_s_invalid_ns_handle",
    0x16c9a0da : "rpc_s_unknown_error",
    0x16c9a0db : "rpc_s_ss_char_trans_open_fail",
    0x16c9a0dc : "rpc_s_ss_char_trans_short_file",
    0x16c9a0dd : "rpc_s_ss_context_damaged",
    0x16c9a0de : "rpc_s_ss_in_null_context",
    0x16c9a0df : "rpc_s_socket_failure",
    0x16c9a0e0 : "rpc_s_unsupported_protect_level",
    0x16c9a0e1 : "rpc_s_invalid_checksum",
    0x16c9a0e2 : "rpc_s_invalid_credentials",
    0x16c9a0e3 : "rpc_s_credentials_too_large",
    0x16c9a0e4 : "rpc_s_call_id_not_found",
    0x16c9a0e5 : "rpc_s_key_id_not_found",
    0x16c9a0e6 : "rpc_s_auth_bad_integrity",
    0x16c9a0e7 : "rpc_s_auth_tkt_expired",
    0x16c9a0e8 : "rpc_s_auth_tkt_nyv",
    0x16c9a0e9 : "rpc_s_auth_repeat",
    0x16c9a0ea : "rpc_s_auth_not_us",
    0x16c9a0eb : "rpc_s_auth_badmatch",
    0x16c9a0ec : "rpc_s_auth_skew",
    0x16c9a0ed : "rpc_s_auth_badaddr",
    0x16c9a0ee : "rpc_s_auth_badversion",
    0x16c9a0ef : "rpc_s_auth_msg_type",
    0x16c9a0f0 : "rpc_s_auth_modified",
    0x16c9a0f1 : "rpc_s_auth_badorder",
    0x16c9a0f2 : "rpc_s_auth_badkeyver",
    0x16c9a0f3 : "rpc_s_auth_nokey",
    0x16c9a0f4 : "rpc_s_auth_mut_fail",
    0x16c9a0f5 : "rpc_s_auth_baddirection",
    0x16c9a0f6 : "rpc_s_auth_method",
    0x16c9a0f7 : "rpc_s_auth_badseq",
    0x16c9a0f8 : "rpc_s_auth_inapp_cksum",
    0x16c9a0f9 : "rpc_s_auth_field_toolong",
    0x16c9a0fa : "rpc_s_invalid_crc",
    0x16c9a0fb : "rpc_s_binding_incomplete",
    0x16c9a0fc : "rpc_s_key_func_not_allowed",
    0x16c9a0fd : "rpc_s_unknown_stub_rtl_if_vers",
    0x16c9a0fe : "rpc_s_unknown_ifspec_vers",
    0x16c9a0ff : "rpc_s_proto_unsupp_by_auth",
    0x16c9a100 : "rpc_s_authn_challenge_malformed",
    0x16c9a101 : "rpc_s_protect_level_mismatch",
    0x16c9a102 : "rpc_s_no_mepv",
    0x16c9a103 : "rpc_s_stub_protocol_error",
    0x16c9a104 : "rpc_s_class_version_mismatch",
    0x16c9a105 : "rpc_s_helper_not_running",
    0x16c9a106 : "rpc_s_helper_short_read",
    0x16c9a107 : "rpc_s_helper_catatonic",
    0x16c9a108 : "rpc_s_helper_aborted",
    0x16c9a109 : "rpc_s_not_in_kernel",
    0x16c9a10a : "rpc_s_helper_wrong_user",
    0x16c9a10b : "rpc_s_helper_overflow",
    0x16c9a10c : "rpc_s_dg_need_way_auth",
    0x16c9a10d : "rpc_s_unsupported_auth_subtype",
    0x16c9a10e : "rpc_s_wrong_pickle_type",
    0x16c9a10f : "rpc_s_not_listening",
    0x16c9a110 : "rpc_s_ss_bad_buffer",
    0x16c9a111 : "rpc_s_ss_bad_es_action",
    0x16c9a112 : "rpc_s_ss_wrong_es_version",
    0x16c9a113 : "rpc_s_fault_user_defined",
    0x16c9a114 : "rpc_s_ss_incompatible_codesets",
    0x16c9a115 : "rpc_s_tx_not_in_transaction",
    0x16c9a116 : "rpc_s_tx_open_failed",
    0x16c9a117 : "rpc_s_partial_credentials",
    0x16c9a118 : "rpc_s_ss_invalid_codeset_tag",
    0x16c9a119 : "rpc_s_mgmt_bad_type",
    0x16c9a11a : "rpc_s_ss_invalid_char_input",
    0x16c9a11b : "rpc_s_ss_short_conv_buffer",
    0x16c9a11c : "rpc_s_ss_iconv_error",
    0x16c9a11d : "rpc_s_ss_no_compat_codeset",
    0x16c9a11e : "rpc_s_ss_no_compat_charsets",
    0x16c9a11f : "dce_cs_c_ok",
    0x16c9a120 : "dce_cs_c_unknown",
    0x16c9a121 : "dce_cs_c_notfound",
    0x16c9a122 : "dce_cs_c_cannot_open_file",
    0x16c9a123 : "dce_cs_c_cannot_read_file",
    0x16c9a124 : "dce_cs_c_cannot_allocate_memory",
    0x16c9a125 : "rpc_s_ss_cleanup_failed",
    0x16c9a126 : "rpc_svc_desc_general",
    0x16c9a127 : "rpc_svc_desc_mutex",
    0x16c9a128 : "rpc_svc_desc_xmit",
    0x16c9a129 : "rpc_svc_desc_recv",
    0x16c9a12a : "rpc_svc_desc_dg_state",
    0x16c9a12b : "rpc_svc_desc_cancel",
    0x16c9a12c : "rpc_svc_desc_orphan",
    0x16c9a12d : "rpc_svc_desc_cn_state",
    0x16c9a12e : "rpc_svc_desc_cn_pkt",
    0x16c9a12f : "rpc_svc_desc_pkt_quotas",
    0x16c9a130 : "rpc_svc_desc_auth",
    0x16c9a131 : "rpc_svc_desc_source",
    0x16c9a132 : "rpc_svc_desc_stats",
    0x16c9a133 : "rpc_svc_desc_mem",
    0x16c9a134 : "rpc_svc_desc_mem_type",
    0x16c9a135 : "rpc_svc_desc_dg_pktlog",
    0x16c9a136 : "rpc_svc_desc_thread_id",
    0x16c9a137 : "rpc_svc_desc_timestamp",
    0x16c9a138 : "rpc_svc_desc_cn_errors",
    0x16c9a139 : "rpc_svc_desc_conv_thread",
    0x16c9a13a : "rpc_svc_desc_pid",
    0x16c9a13b : "rpc_svc_desc_atfork",
    0x16c9a13c : "rpc_svc_desc_cma_thread",
    0x16c9a13d : "rpc_svc_desc_inherit",
    0x16c9a13e : "rpc_svc_desc_dg_sockets",
    0x16c9a13f : "rpc_svc_desc_timer",
    0x16c9a140 : "rpc_svc_desc_threads",
    0x16c9a141 : "rpc_svc_desc_server_call",
    0x16c9a142 : "rpc_svc_desc_nsi",
    0x16c9a143 : "rpc_svc_desc_dg_pkt",
    0x16c9a144 : "rpc_m_cn_ill_state_trans_sa",
    0x16c9a145 : "rpc_m_cn_ill_state_trans_ca",
    0x16c9a146 : "rpc_m_cn_ill_state_trans_sg",
    0x16c9a147 : "rpc_m_cn_ill_state_trans_cg",
    0x16c9a148 : "rpc_m_cn_ill_state_trans_sr",
    0x16c9a149 : "rpc_m_cn_ill_state_trans_cr",
    0x16c9a14a : "rpc_m_bad_pkt_type",
    0x16c9a14b : "rpc_m_prot_mismatch",
    0x16c9a14c : "rpc_m_frag_toobig",
    0x16c9a14d : "rpc_m_unsupp_stub_rtl_if",
    0x16c9a14e : "rpc_m_unhandled_callstate",
    0x16c9a14f : "rpc_m_call_failed",
    0x16c9a150 : "rpc_m_call_failed_no_status",
    0x16c9a151 : "rpc_m_call_failed_errno",
    0x16c9a152 : "rpc_m_call_failed_s",
    0x16c9a153 : "rpc_m_call_failed_c",
    0x16c9a154 : "rpc_m_errmsg_toobig",
    0x16c9a155 : "rpc_m_invalid_srchattr",
    0x16c9a156 : "rpc_m_nts_not_found",
    0x16c9a157 : "rpc_m_invalid_accbytcnt",
    0x16c9a158 : "rpc_m_pre_v2_ifspec",
    0x16c9a159 : "rpc_m_unk_ifspec",
    0x16c9a15a : "rpc_m_recvbuf_toosmall",
    0x16c9a15b : "rpc_m_unalign_authtrl",
    0x16c9a15c : "rpc_m_unexpected_exc",
    0x16c9a15d : "rpc_m_no_stub_data",
    0x16c9a15e : "rpc_m_eventlist_full",
    0x16c9a15f : "rpc_m_unk_sock_type",
    0x16c9a160 : "rpc_m_unimp_call",
    0x16c9a161 : "rpc_m_invalid_seqnum",
    0x16c9a162 : "rpc_m_cant_create_uuid",
    0x16c9a163 : "rpc_m_pre_v2_ss",
    0x16c9a164 : "rpc_m_dgpkt_pool_corrupt",
    0x16c9a165 : "rpc_m_dgpkt_bad_free",
    0x16c9a166 : "rpc_m_lookaside_corrupt",
    0x16c9a167 : "rpc_m_alloc_fail",
    0x16c9a168 : "rpc_m_realloc_fail",
    0x16c9a169 : "rpc_m_cant_open_file",
    0x16c9a16a : "rpc_m_cant_read_addr",
    0x16c9a16b : "rpc_svc_desc_libidl",
    0x16c9a16c : "rpc_m_ctxrundown_nomem",
    0x16c9a16d : "rpc_m_ctxrundown_exc",
    0x16c9a16e : "rpc_s_fault_codeset_conv_error",
    0x16c9a16f : "rpc_s_no_call_active",
    0x16c9a170 : "rpc_s_cannot_support",
    0x16c9a171 : "rpc_s_no_context_available",
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
            self['pduData'] = b''
            self['auth_data'] = b''
            self['sec_trailer'] = b''
            self['pad'] = b''

    def get_header_size(self):
        return self._SIZE + (16 if (self["flags"] & PFC_OBJECT_UUID) > 0 else 0)

    def get_packet(self):
        if self['auth_data'] != b'':
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
           self['uuid'] = b''

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
            self['ctx_items'] = b''
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
            self['Pad'] = b''
            self['ctx_items'] = b''
            self['sec_trailer'] = b''
            self['auth_data'] = b''

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
            self['SupportedVersions'] = b''
