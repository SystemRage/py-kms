#!/usr/bin/env python3

import logging
import binascii
import hashlib
import random
import struct

from kmsBase import kmsBase
from structure import Structure
import aes
from formatText import justify, shell_message, byterize

class kmsRequestV5(kmsBase):
        class RequestV5(Structure):
                class Message(Structure):
                        commonHdr = ()
                        structure = (
                                ('salt',      '16s'),
                                ('encrypted', '236s'), #kmsBase.kmsRequestStruct
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
                        ('bodyLength1',  '<I=2 + 2 + len(salt) + len(encrypted)'),
                        ('unknown',      '!I=0x00000200'),
                        ('bodyLength2',  '<I=2 + 2 + len(salt) + len(encrypted)'),
                        ('versionMinor', '<H'),
                        ('versionMajor', '<H'),
                        ('salt',         '16s'),
                        ('encrypted',    ':'), #DecryptedResponse
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
                self.requestData = self.RequestV5(self.data)
        
                decrypted = self.decryptRequest(self.requestData)

                responseBuffer = self.serverLogic(decrypted['request'])
        
                iv, encrypted = self.encryptResponse(self.requestData, decrypted, responseBuffer)

                self.responseData = self.generateResponse(iv, encrypted)
        
        def decryptRequest(self, request):
                encrypted = bytearray(str(request['message']).encode('latin-1')) #*2to3*
                iv = bytearray(request['message']['salt'].encode('latin-1')) #*2to3*
                moo = aes.AESModeOfOperation()
                moo.aes.v6 = self.v6
                decrypted = moo.decrypt(encrypted, 256, moo.ModeOfOperation["CBC"], self.key, moo.aes.KeySize["SIZE_128"], iv) #*2to3*
                decrypted = aes.strip_PKCS7_padding(decrypted)
                decrypted = bytes(decrypted) #*2to3*

                return self.DecryptedRequest(decrypted)

        def encryptResponse(self, request, decrypted, response):
                randomSalt = self.getRandomSalt()
                sha256 = hashlib.sha256()
                sha256.update(randomSalt) #*2to3*
                result = sha256.digest()
                
                iv = bytearray(request['message']['salt'].encode('latin-1')) #*2to3*

                randomStuff = bytearray(16)
                for i in range(0,16):
                        randomStuff[i] = (bytearray(decrypted['salt'].encode('latin-1'))[i] ^ iv[i] ^ randomSalt[i]) & 0xff #*2to3*

                responsedata = self.DecryptedResponse()
                responsedata['response'] = response
                responsedata['keys'] = randomStuff #*2to3*
                responsedata['hash'] = result
                
                padded = aes.append_PKCS7_padding(str(responsedata).encode('latin-1')) #*2to3*
                moo = aes.AESModeOfOperation()
                moo.aes.v6 = self.v6
                mode, orig_len, crypted = moo.encrypt(padded, moo.ModeOfOperation["CBC"], self.key, moo.aes.KeySize["SIZE_128"], iv) #*2to3*

                return iv.decode('latin-1').encode('latin-1'), crypted #*2to3*
        

        def decryptResponse(self, response):
                paddingLength = response['bodyLength1'] % 8
                iv = bytearray(response['salt'].encode('latin-1')) #*2to3*
                encrypted = bytearray(response['encrypted'][:-paddingLength].encode('latin-1')) #*2to3*
                moo = aes.AESModeOfOperation()
                moo.aes.v6 = self.v6
                decrypted = moo.decrypt(encrypted, 256, moo.ModeOfOperation["CBC"], self.key, moo.aes.KeySize["SIZE_128"], iv) #*2to3*
                decrypted = aes.strip_PKCS7_padding(decrypted)
                decrypted = bytes(decrypted) #*2to3*

                return self.DecryptedResponse(decrypted)
                
        def getRandomSalt(self):
                return bytearray(random.getrandbits(8) for i in range(16))
        
        def generateResponse(self, iv, encryptedResponse):
                bodyLength = 4 + len(iv) + len(encryptedResponse)
                response = self.ResponseV5()
                response['versionMinor'] = self.requestData['versionMinor']
                response['versionMajor'] = self.requestData['versionMajor']
                response['salt'] = iv
                response['encrypted'] = bytes(encryptedResponse) #*2to3*
                response['padding'] = self.getResponsePadding(bodyLength).decode('latin-1').encode('latin-1') #*2to3*
                
                shell_message(nshell = 16)
                response = byterize(response) 
                logging.info("KMS V%d Response: \n%s\n" % (self.ver, justify(response.dump(print_to_stdout = False))))
                logging.info("KMS V%d Structure Bytes: \n%s\n" % (self.ver, justify(binascii.b2a_hex(str(response).encode('latin-1')).decode('utf-8')))) #*2to3*
                                                        
                return str(response)
        
        def getResponse(self):
                return self.responseData

        def generateRequest(self, requestBase):
                esalt = self.getRandomSalt()

                moo = aes.AESModeOfOperation()
                moo.aes.v6 = self.v6
                dsalt = moo.decrypt(esalt, 16, moo.ModeOfOperation["CBC"], self.key, moo.aes.KeySize["SIZE_128"], esalt) #*2to3*
                dsalt = bytearray(dsalt)

                decrypted = self.DecryptedRequest()
                decrypted['salt'] = dsalt #*2to3*
                decrypted['request'] = requestBase

                padded = aes.append_PKCS7_padding(str(decrypted).encode('latin-1')) #*2to3*
                mode, orig_len, crypted = moo.encrypt(padded, moo.ModeOfOperation["CBC"], self.key, moo.aes.KeySize["SIZE_128"], esalt) #*2to3*

                message = self.RequestV5.Message(bytes(crypted)) #*2to3*

                bodyLength = len(message) + 2 + 2

                request = self.RequestV5()
                request['bodyLength1'] = bodyLength
                request['bodyLength2'] = bodyLength
                request['versionMinor'] = requestBase['versionMinor']
                request['versionMajor'] = requestBase['versionMajor']
                request['message'] = message

                shell_message(nshell = 10)
                request = byterize(request)
                logging.info("Request V%d Data: \n%s\n" % (self.ver, justify(request.dump(print_to_stdout = False))))
                logging.info("Request V%d: \n%s\n" % (self.ver, justify(binascii.b2a_hex(str(request).encode('latin-1')).decode('utf-8')))) #*2to3*
                
                return request
