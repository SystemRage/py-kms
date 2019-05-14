#!/usr/bin/env python3

import hashlib
import hmac
import struct

import pykms_Aes as aes
from pykms_Base import kmsBase
from pykms_RequestV5 import kmsRequestV5
from pykms_Structure import Structure
from pykms_Format import enco, deco

#---------------------------------------------------------------------------------------------------------------------------------------------------------

class kmsRequestV6(kmsRequestV5):
        class DecryptedResponse(Structure):
                class Message(Structure):
                        commonHdr = ()
                        structure = (
                                ('response', ':', kmsBase.kmsResponseStruct),
                                ('keys',     '16s'),
                                ('hash',     '32s'),
                                ('hwid',     '8s'),
                                ('xorSalts', '16s'),
                        )

                commonHdr = ()
                structure = (
                        ('message', ':', Message),
                        ('hmac',    '16s'),
                )

        key = bytearray([ 0xA9, 0x4A, 0x41, 0x95, 0xE2, 0x01, 0x43, 0x2D, 0x9B, 0xCB, 0x46, 0x04, 0x05, 0xD8, 0x4A, 0x21 ])

        v6 = True

        ver = 6

        def encryptResponse(self, request, decrypted, response):
                randomSalt = self.getRandomSalt()
                result = hashlib.sha256(randomSalt).digest()

                SaltC = bytearray(enco(request['message']['salt'], 'latin-1'))
                DSaltC = bytearray(enco(decrypted['salt'], 'latin-1'))

                randomStuff = bytearray(16)
                for i in range(0,16):
                        randomStuff[i] = (SaltC[i] ^ DSaltC[i] ^ randomSalt[i]) & 0xff

                # XorSalts
                XorSalts = bytearray(16)
                for i in range (0, 16):
                        XorSalts[i] = (SaltC[i] ^ DSaltC[i]) & 0xff

                message = self.DecryptedResponse.Message()
                message['response'] = response
                message['keys'] = bytes(randomStuff)
                message['hash'] = result
                message['xorSalts'] = bytes(XorSalts)
                message['hwid'] = self.srv_config['hwid']

                # SaltS
                SaltS = self.getRandomSalt()

                moo = aes.AESModeOfOperation()
                moo.aes.v6 = True
                decry = moo.decrypt(SaltS, 16, moo.ModeOfOperation["CBC"], self.key, moo.aes.KeySize["SIZE_128"], SaltS)

                # DSaltS
                DSaltS = bytearray(decry)

                # HMacMsg
                HMacMsg = bytearray(16)
                for i in range(0,16):
                        HMacMsg[i] = (SaltS[i] ^ DSaltS[i]) & 0xff
                HMacMsg.extend(enco(str(message), 'latin-1'))

                # HMacKey
                requestTime = decrypted['request']['requestTime']
                HMacKey = self.getMACKey(requestTime)                
                HMac = hmac.new(HMacKey, bytes(HMacMsg), hashlib.sha256)
                digest = HMac.digest()

                responsedata = self.DecryptedResponse()
                responsedata['message'] = message
                responsedata['hmac'] = digest[16:]

                padded = aes.append_PKCS7_padding(enco(str(responsedata), 'latin-1'))
                mode, orig_len, crypted = moo.encrypt(padded, moo.ModeOfOperation["CBC"], self.key, moo.aes.KeySize["SIZE_128"], SaltS)

                return bytes(SaltS), bytes(bytearray(crypted))
        

        def getMACKey(self, t):
                c1 = 0x00000022816889BD
                c2 = 0x000000208CBAB5ED
                c3 = 0x3156CD5AC628477A

                i1 = (t // c1) & 0xFFFFFFFFFFFFFFFF
                i2 = (i1 * c2) & 0xFFFFFFFFFFFFFFFF
                seed = (i2 + c3) & 0xFFFFFFFFFFFFFFFF

                sha256 = hashlib.sha256()
                sha256.update(struct.pack("<Q", seed))
                digest = sha256.digest()

                return digest[16:]
        
