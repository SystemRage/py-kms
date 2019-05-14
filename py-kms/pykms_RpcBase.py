#!/usr/bin/env python3

class rpcBase:
        packetType = {
                'request':              0,
                'ping':                 1,
                'response':             2,
                'fault':                3,
                'working':              4,
                'nocall':               5,
                'reject':               6,
                'ack':                  7,
                'clCancel':             8,
                'fack':                 9,
                'cancelAck':            10,
                'bindReq':              11,
                'bindAck':              12,
                'bindNak':              13,
                'alterContext':         14,
                'alterContextResp':     15,
                'shutdown':             17,
                'coCancel':             18,
                'orphaned':             19
        }

        packetFlags = {
                'firstFrag':            1,  # 0x01
                'lastFrag':             2,  # 0x02
                'cancelPending':        4,  # 0x04
                'reserved':             8,  # 0x08
                'multiplex':            16, # 0x10
                'didNotExecute':        32, # 0x20
                'maybe':                64, # 0x40
                'objectUuid':           128 # 0x80
        }

        def __init__(self, data, srv_config):
                self.data = data
                self.srv_config = srv_config

        def populate(self):
                return self.generateResponse(self.parseRequest())

        def parseRequest(self):
                return {}
