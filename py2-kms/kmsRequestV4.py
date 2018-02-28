#!/usr/bin/env python

import binascii
import struct
import time
import logging

from kmsBase import kmsBase
from structure import Structure
from aes import AES
from formatText import shell_message, justify

# v4 AES Key
key = bytearray([0x05, 0x3D, 0x83, 0x07, 0xF9, 0xE5, 0xF0, 0x88, 0xEB, 0x5E, 0xA6, 0x68, 0x6C, 0xF0, 0x37, 0xC7, 0xE4, 0xEF, 0xD2, 0xD6])

# Xor Buffer
def xorBuffer(source, offset, destination, size):
	for i in range(0, size):
		destination[i] ^= source[i + offset]

class kmsRequestV4(kmsBase):
	class RequestV4(Structure):
		commonHdr = ()
		structure = (
			('bodyLength1', '<I'),
			('bodyLength2', '<I'),
			('request',     ':', kmsBase.kmsRequestStruct),
			('hash',        '16s'),
			('padding',     ':'),
		)

	class ResponseV4(Structure):
		commonHdr = ()
		structure = (
			('bodyLength1', '<I=len(response) + len(hash)'),
			('unknown',     '!I=0x00000200'),
			('bodyLength2', '<I=len(response) + len(hash)'),
			('response',    ':', kmsBase.kmsResponseStruct),
			('hash',        '16s'),
			('padding',     ':'),
		)

	def executeRequestLogic(self):
		requestData = self.RequestV4(self.data)

		response = self.serverLogic(requestData['request'])
		hash = self.generateHash(bytearray(str(response)))

		self.responseData = self.generateResponse(response, hash)

		time.sleep(1) # request sent back too quick for Windows 2008 R2, slow it down.

	def generateHash(self, message):
		"""
		The KMS v4 hash is a variant of CMAC-AES-128. There are two key differences:
		* The 'AES' used is modified in particular ways:
		  * The basic algorithm is Rjindael with a conceptual 160bit key and 128bit blocks.
		    This isn't part of the AES standard, but it works the way you'd expect.
		    Accordingly, the algorithm uses 11 rounds and a 192 byte expanded key.
		* The trailing block is not XORed with a generated subkey, as defined in CMAC.
		  This is probably because the subkey generation algorithm is only defined for
		  situations where block and key size are the same.
		"""
		aes = AES()

		messageSize = len(message)
		lastBlock = bytearray(16) 
		hashBuffer = bytearray(16)

		# MessageSize / Blocksize
		j = messageSize >> 4

		# Remainding bytes
		k = messageSize & 0xf

		# Hash
		for i in range(0, j):
			xorBuffer(message, i << 4, hashBuffer, 16)
			hashBuffer = bytearray(aes.encrypt(hashBuffer, key, len(key)))

		# Bit Padding
		ii = 0
		for i in range(j << 4, k + (j << 4)):
			lastBlock[ii] = message[i]
			ii += 1
		lastBlock[k] = 0x80

		xorBuffer(lastBlock, 0, hashBuffer, 16)
		hashBuffer = bytearray(aes.encrypt(hashBuffer, key, len(key)))

		return str(hashBuffer)

	def generateResponse(self, responseBuffer, hash):
		bodyLength = len(responseBuffer) + len(hash)
		response = self.ResponseV4()
		response['response'] = responseBuffer
		response['hash'] = hash
		response['padding'] = self.getResponsePadding(bodyLength)
		
		shell_message(nshell = 16)                
                logging.debug("KMS V4 Response: %s" % justify(response.dump(print_to_stdout = False)))
                logging.debug("KMS V4 Response Bytes: %s" % justify(binascii.b2a_hex(str(response))))
			
		return str(response)

	def getResponse(self):
		return self.responseData

	def generateRequest(self, requestBase):
		hash = str(self.generateHash(bytearray(str(requestBase))))

		bodyLength = len(requestBase) + len(hash)

		request = kmsRequestV4.RequestV4()
		request['bodyLength1'] = bodyLength
		request['bodyLength2'] = bodyLength
		request['request'] = requestBase
		request['hash'] = hash
		request['padding'] = self.getResponsePadding(bodyLength)
		
		shell_message(nshell = 10)                
                logging.debug("Request V4 Data: %s" % justify(request.dump(print_to_stdout = False)))
                logging.debug("Request V4: %s" % justify(binascii.b2a_hex(str(request))))
                        
		return request
