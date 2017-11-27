import hashlib
import json

from time import time
from uuid import uuid4
from textwrap import dedent
from flask import Flask, jsonify, request


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        #Create the genesis block
        self.new_block(1,100)

    def proof_of_work(self, last_proof):
        '''
        Proof of work algorithm:
        - Find a number x so that hash(px) has 4 leading zeroes
        - p is the previous proof, and x is the new proof
        '''

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        # Validates the proof by checking if it has 4 leading zeroes
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


    def new_block(self,previous_hash,last_proof):
        # Function for adding a new block to the chain

        block = {
            'index': len(self.chain) + 1,
            'timestamp':time(),
            'transactions':self.current_transactions,
            # The proof from the proof work algorithm
            'proof':self.proof_of_work(last_proof),
            # Hash of the previous block
            'previous_hash':previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the list of current transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        # Creates a new transaction to go into the next mined Block

        self.current_transactions.append({
            # Address of the sender
            'sender':sender,
            # Address of the recipient
            'recipient':recipient,
            # The size of the transaction
            'amount':amount,
        })

        # The next block, which will hold the transaction
        return self.last_block['index'] + 1



    @staticmethod
    def hash(block):
        # Hashes a block
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        # Return the last block in the chain
        return self.chain[-1]


# Initiate my node
app = Flask(__name__)

# Generate a globally unique node Address
node_identifier = str(uuid4()).replace('-','')

# Start the blockchain
blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    # Run the proof of work algorithm to get the next proof
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # Reward the miner for finding the proof
    # Sender is 0 to signify that this is a newly mined coin
    blockchain.new_transaction(
        sender='0',
        recipient=node_identifier,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)


    response = {
        'message': 'New block forged',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }

    return jsonify(reponse), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check to see that requred fields are in the POSTed data
    required = ['sender','recipient','amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create new transacrion
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    # Create feedback for the user
    response = {'message':f'Transction will be added to block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain':blockchain.chain,
        'length':len(blockchain.chain),
    }
    return jsonify(reponse), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
