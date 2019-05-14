#!/usr/bin/env python3

import struct

from pykms_Base import kmsBase
from pykms_Misc import ErrorCodes

#---------------------------------------------------------------------------------------------------------------------------------------------------------

class kmsRequestUnknown(kmsBase):
        def executeRequestLogic(self):
                finalResponse = bytearray()
                finalResponse.extend(bytearray(struct.pack('<I', 0)))
                finalResponse.extend(bytearray(struct.pack('<I', 0)))
                finalResponse.extend(bytearray(struct.pack('<I', ErrorCodes['SL_E_VL_KEY_MANAGEMENT_SERVICE_ID_MISMATCH'][0])))
                return finalResponse.decode('utf-8').encode('utf-8')
