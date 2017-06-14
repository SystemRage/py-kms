import binascii
import kmsBase
import rpcBase
import struct
import uuid
from dcerpc import MSRPCRequestHeader, MSRPCRespHeader
import logging

class handler(rpcBase.rpcBase):
	def parseRequest(self):
		request = MSRPCRequestHeader(self.data)
		logging.debug("RPC Message Request Bytes: %s" % binascii.b2a_hex(self.data))
		logging.debug("RPC Message Request: %s" % request.dump())
		
		return request

	def generateResponse(self):
		request = self.requestData

		responseData = kmsBase.generateKmsResponseData(request['pduData'], self.config)
		envelopeLength = len(responseData)

		response = MSRPCRespHeader()
		response['ver_major'] = request['ver_major']
		response['ver_minor'] = request['ver_minor']
		response['type'] = self.packetType['response']
		response['flags'] = self.packetFlags['firstFrag'] | self.packetFlags['lastFrag']
		response['representation'] = request['representation']
		response['call_id'] = request['call_id']

		response['alloc_hint'] = envelopeLength
		response['ctx_id'] = request['ctx_id']
		response['cancel_count'] = 0

		response['pduData'] = responseData

		logging.debug("RPC Message Response: %s" % response.dump())
		logging.debug("RPC Message Response Bytes: %s" % binascii.b2a_hex(str(response)))

		return response

	def generateRequest(self):
		request = MSRPCRequestHeader()

		request['ver_major'] = 5
		request['ver_minor'] = 0
		request['type'] = self.packetType['request']
		request['flags'] = self.packetFlags['firstFrag'] | self.packetFlags['lastFrag']
		request['representation'] = 0x10
		request['call_id'] = self.config['call_id']
		request['alloc_hint'] = len(self.data)
		request['pduData'] = str(self.data)

		logging.debug("RPC Message Request: %s" % request.dump())
		logging.debug("RPC Message Request Bytes: %s" % binascii.b2a_hex(str(request)))

		return request

	def parseResponse(self):
		return response
