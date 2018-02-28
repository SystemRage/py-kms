#!/usr/bin/env python3

import struct

from kmsBase import kmsBase

class kmsRequestUnknown(kmsBase):
        def getResponse(self):
                finalResponse = bytearray()
                finalResponse.extend(bytearray(struct.pack('<I', 0)))
                finalResponse.extend(bytearray(struct.pack('<I', 0)))
                finalResponse.extend(bytearray(struct.pack('<I', self.errorCodes['SL_E_VL_KEY_MANAGEMENT_SERVICE_ID_MISMATCH'])))
                return finalResponse.decode('utf-8').encode('utf-8') #*2to3*
