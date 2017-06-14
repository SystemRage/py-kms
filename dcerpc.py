# Copyright (c) 2003-2012 CORE Security Technologies
#
# This software is provided under under a slightly modified version
# of the Apache Software License. See the accompanying LICENSE file
# for more information.
#
# $Id: dcerpc.py 917 2013-11-10 20:47:57Z bethus $
#
# Partial C706.pdf + [MS-RPCE] implementation
#
# ToDo: 
# [ ] Take out all the security provider stuff out of here (e.g. RPC_C_AUTHN_WINNT)
#     and put it elsewhere. This will make the coder cleaner and easier to add 
#     more SSP (e.g. NETLOGON)
# 

from structure import Structure,pack,unpack

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
MSRPC_FIRSTFRAG     = 0x01
MSRPC_LASTFRAG      = 0x02

# For PDU types bind, bind_ack, alter_context, and
# alter_context_resp, this flag MUST be interpreted as PFC_SUPPORT_HEADER_SIGN
MSRPC_SUPPORT_SIGN  = 0x04

#For the
#remaining PDU types, this flag MUST be interpreted as PFC_PENDING_CANCEL.
MSRPC_PENDING_CANCEL= 0x04

MSRPC_NOTAFRAG      = 0x04
MSRPC_RECRESPOND    = 0x08
MSRPC_NOMULTIPLEX   = 0x10
MSRPC_NOTFORIDEMP   = 0x20
MSRPC_NOTFORBCAST   = 0x40
MSRPC_NOUUID        = 0x80

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
    0x1C000025L : 'nca_s_fault_no_client_stub'
}

class Exception(Exception):
    pass

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
        ('frag_len','<H=self._SIZE+len(pduData)+len(pad)+len(sec_trailer)+len(auth_data)'),  # 8
        ('auth_len','<H=len(auth_data)'),                 # 10
        ('call_id','<L=1'),                               # 12    <-- Common up to here (including this)
    )

    structure = ( 
        ('dataLen','_-pduData','self["frag_len"]-self["auth_len"]-self._SIZE-(8 if self["auth_len"] > 0 else 0)'),  
        ('pduData',':'),                                
        ('_pad', '_-pad','(4 - ((self._SIZE + len(self["pduData"])) & 3) & 3)'),
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
            self['flags'] = MSRPC_FIRSTFRAG | MSRPC_LASTFRAG 
            self['type'] = MSRPC_REQUEST
            self.__frag_len_set = 0
            self['auth_len'] = 0
            self['pduData'] = ''
            self['auth_data'] = ''
            self['sec_trailer'] = ''
            self['pad'] = ''

    def get_header_size(self):
        return self._SIZE

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
    )

    def __init__(self, data = None, alignment = 0):
        MSRPCHeader.__init__(self, data, alignment)
        if data is None:
           self['type'] = MSRPC_REQUEST
           self['ctx_id'] = 0

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

class MSRPCBindAck(Structure):
    _SIZE = 26 # Up to SecondaryAddr
    _CTX_ITEM_LEN = len(CtxItemResult())
    commonHdr = ( 
        ('ver_major','B=5'),                            # 0
        ('ver_minor','B=0'),                            # 1
        ('type','B=0'),                                 # 2
        ('flags','B=0'),                                # 3
        ('representation','<L=0x10'),                   # 4
        ('frag_len','<H=0'),                            # 8
        ('auth_len','<H=0'),                            # 10
        ('call_id','<L=1'),                             # 12    <-- Common up to here (including this)
    )
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
        Structure.__init__(self,data,alignment)
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
