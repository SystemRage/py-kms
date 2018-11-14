#!/usr/bin/env python

import logging
import binascii
import hashlib
import random

import aes
from kmsBase import kmsBase
from structure import Structure
from formatText import justify, shell_message

class kmsRequestV5(kmsBase):
        class RequestV5(Structure):
                class Message(Structure):
                        commonHdr = ()
                        structure = (
                                ('salt',      '16s'),
                                ('encrypted', '240s'), # kmsBase.kmsRequestStruct
                                ('padding',   ':'),
                        )

                commonHdr = ()
                structure = (
                        ('bodyLength1',  '<I'),  
                        ('bodyLength2',  '<I'), 
                        ('versionMinor', '<H'),
                        ('versionMajor', '<H'),
                        ('message',      ':', Message),
                )

        class DecryptedRequest(Structure):
                commonHdr = ()
                structure = (
                        ('salt',    '16s'),
                        ('request', ':', kmsBase.kmsRequestStruct),
                )

        class ResponseV5(Structure):
                commonHdr = ()
                structure = (
                        ('bodyLength1',  '<I'),
                        ('unknown',      '!I=0x00000200'),
                        ('bodyLength2',  '<I'),
                        ('versionMinor', '<H'),
                        ('versionMajor', '<H'),
                        ('salt',         '16s'),
                        ('encrypted',    ':'), # DecryptedResponse
                        ('padding',      ':'),
                )

        class DecryptedResponse(Structure):
                commonHdr = ()
                structure = (
                        ('response', ':', kmsBase.kmsResponseStruct),
                        ('keys',     '16s'),
                        ('hash',     '32s'),
                )

        key = bytearray([ 0xCD, 0x7E, 0x79, 0x6F, 0x2A, 0xB2, 0x5D, 0xCB, 0x55, 0xFF, 0xC8, 0xEF, 0x83, 0x64, 0xC4, 0x70 ])

        v6 = False

        ver = 5

        def executeRequestLogic(self):
                requestData = self.RequestV5(self.data) 
        
                decrypted = self.decryptRequest(requestData)

                responseBuffer = self.serverLogic(decrypted['request'])
        
                iv, encrypted = self.encryptResponse(requestData, decrypted, responseBuffer)

                responseData = self.generateResponse(iv, encrypted, requestData)
                
                return responseData
        
        def decryptRequest(self, request):
                encrypted = bytearray(str(request['message']))
                iv = bytearray(request['message']['salt'])

                moo = aes.AESModeOfOperation()
                moo.aes.v6 = self.v6
                decrypted = moo.decrypt(encrypted, 256, moo.modeOfOperation["CBC"], self.key, moo.aes.keySize["SIZE_128"], iv)
                decrypted = aes.strip_PKCS7_padding(decrypted)

                return self.DecryptedRequest(decrypted)

        def encryptResponse(self, request, decrypted, response):
                randomSalt = self.getRandomSalt()
                result = hashlib.sha256(str(randomSalt)).digest()
                iv = bytearray(request['message']['salt'])

                randomStuff = bytearray(16)
                for i in range(0,16):
                        randomStuff[i] = (bytearray(decrypted['salt'])[i] ^ iv[i] ^ randomSalt[i]) & 0xff

                responsedata = self.DecryptedResponse()
                responsedata['response'] = response
                responsedata['keys'] = str(randomStuff)
                responsedata['hash'] = result
                
                padded = aes.append_PKCS7_padding(str(responsedata))
                moo = aes.AESModeOfOperation()
                moo.aes.v6 = self.v6
                mode, orig_len, crypted = moo.encrypt(padded, moo.modeOfOperation["CBC"], self.key, moo.aes.keySize["SIZE_128"], iv)

                return str(iv), str(bytearray(crypted))

        def decryptResponse(self, response):
                paddingLength = self.getPadding(response['bodyLength1'])
                
                iv = bytearray(response['salt'])
                encrypted = bytearray(response['encrypted'][:-paddingLength])
                moo = aes.AESModeOfOperation()
                moo.aes.v6 = self.v6
                decrypted = moo.decrypt(encrypted, 256, moo.modeOfOperation["CBC"], self.key, moo.aes.keySize["SIZE_128"], iv)
                decrypted = aes.strip_PKCS7_padding(decrypted)

                return self.DecryptedResponse(decrypted)
                
        def getRandomSalt(self):
                return bytearray(random.getrandbits(8) for i in range(16))
        
        def generateResponse(self, iv, encryptedResponse, requestData):                
                response = self.ResponseV5()
                bodyLength = 2 + 2 + len(iv) + len(encryptedResponse)
                response['bodyLength1'] = bodyLength
                response['bodyLength2'] = bodyLength
                response['versionMinor'] = requestData['versionMinor']
                response['versionMajor'] = requestData['versionMajor']
                response['salt'] = iv
                response['encrypted'] = encryptedResponse
                response['padding'] = bytearray(self.getPadding(bodyLength))
                
                shell_message(nshell = 16)
                logging.info("KMS V%d Response: \n%s\n" % (self.ver, justify(response.dump(print_to_stdout = False))))
                logging.info("KMS V%d Structure Bytes: \n%s\n" % (self.ver, justify(binascii.b2a_hex(str(response)))))
                        
                return str(response)

        def generateRequest(self, requestBase):
                esalt = self.getRandomSalt()

                moo = aes.AESModeOfOperation()
                moo.aes.v6 = self.v6
                dsalt = moo.decrypt(esalt, 16, moo.modeOfOperation["CBC"], self.key, moo.aes.keySize["SIZE_128"], esalt)
                dsalt = bytearray(dsalt)

                decrypted = self.DecryptedRequest()
                decrypted['salt'] = str(dsalt)
                decrypted['request'] = requestBase

                padded = aes.append_PKCS7_padding(str(decrypted))
                mode, orig_len, crypted = moo.encrypt(padded, moo.modeOfOperation["CBC"], self.key, moo.aes.keySize["SIZE_128"], esalt)

                message = self.RequestV5.Message(str(bytearray(crypted)))

                request = self.RequestV5()
                bodyLength = 2 + 2 + len(message)
                request['bodyLength1'] = bodyLength
                request['bodyLength2'] = bodyLength
                request['versionMinor'] = requestBase['versionMinor']
                request['versionMajor'] = requestBase['versionMajor']
                request['message'] = message

                shell_message(nshell = 10)
                logging.info("Request V%d Data: \n%s\n" % (self.ver, justify(request.dump(print_to_stdout = False))))
                logging.info("Request V%d: \n%s\n" % (self.ver, justify(binascii.b2a_hex(str(request)))))
                                
                return request
