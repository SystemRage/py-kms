import aes
import binascii
import hashlib
import hmac
import random
import struct
from kmsBase import kmsBase
from kmsRequestV5 import kmsRequestV5
from structure import Structure

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
		sha256 = hashlib.sha256()
		sha256.update(str(randomSalt))
		result = sha256.digest()

		SaltC = bytearray(request['message']['salt'])
		DSaltC = bytearray(decrypted['salt'])

		randomStuff = bytearray(16)
		for i in range(0,16):
			randomStuff[i] = (SaltC[i] ^ DSaltC[i] ^ randomSalt[i]) & 0xff

		# XorSalts
		XorSalts = bytearray(16)
		for i in range (0, 16):
			XorSalts[i] = (SaltC[i] ^ DSaltC[i]) & 0xff

		message = self.DecryptedResponse.Message()
		message['response'] = response
		message['keys'] = str(randomStuff)
		message['hash'] = result
		message['xorSalts'] = str(XorSalts)
		message['hwid'] = self.config['hwid']

		# SaltS
		SaltS = self.getRandomSalt()

		moo = aes.AESModeOfOperation()
		moo.aes.v6 = True
		d = moo.decrypt(SaltS, 16, moo.modeOfOperation["CBC"], self.key, moo.aes.keySize["SIZE_128"], SaltS)

		# DSaltS
		DSaltS = bytearray(d)

		# HMacMsg
		HMacMsg = bytearray(16)
		for i in range (0, 16):
			HMacMsg[i] = (SaltS[i] ^ DSaltS[i]) & 0xff
		HMacMsg.extend(str(message))

		# HMacKey
		requestTime = decrypted['request']['requestTime']
		HMacKey = self.getMACKey(requestTime)
		HMac = hmac.new(HMacKey, str(HMacMsg), hashlib.sha256)
		digest = HMac.digest()

		responsedata = self.DecryptedResponse()
		responsedata['message'] = message
		responsedata['hmac'] = digest[16:]

		padded = aes.append_PKCS7_padding(str(responsedata))
		mode, orig_len, crypted = moo.encrypt(str(padded), moo.modeOfOperation["CBC"], self.key, moo.aes.keySize["SIZE_128"], SaltS)

		return str(SaltS), str(bytearray(crypted))

	def getMACKey(self, t):
		c1 = 0x00000022816889BD
		c2 = 0x000000208CBAB5ED
		c3 = 0x3156CD5AC628477A

		i1 = (t / c1) & 0xFFFFFFFFFFFFFFFF
		i2 = (i1 * c2) & 0xFFFFFFFFFFFFFFFF
		seed = (i2 + c3) & 0xFFFFFFFFFFFFFFFF

		sha256 = hashlib.sha256()
		sha256.update(struct.pack("<Q", seed))
		digest = sha256.digest()

		return digest[16:]

