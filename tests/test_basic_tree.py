#!/usr/bin/env python

import logging

import blocks
from structs import Rect

class VerificationQuad(blocks.Quad):
	def __eq__(self, other):
		these_quads_match = (self.rect == other.rect)
		if not these_quads_match:
			logging.debug('Core Rect Mismatch: %s != %s' % (
				self.rect, other.rect))
			return False

		self_charges_len = len(self.charges)
		other_charges_len = len(other.charges)
		charges_same_len = (self_charges_len == other_charges_len)
		if not charges_same_len:
			logging.debug('Charges Length Mismatch: %s != %s' % (
				self_charges_len, other_charges_len))
			return False

		charges_match = (list(self.charges) == list(other.charges))
		if not charges_match:
			logging.debug('Charges Mismatch: %s != %s' % (
				self.charges, other.charges))
			return False

		self_sub_quads = [quad for quad in self.quads if quad is not None]
		other_sub_quads = [quad for quad in other.quads if quad is not None]
		sub_quads_same_len = len(self_sub_quads) == len(other_sub_quads)
		if not sub_quads_same_len:
			logging.debug('Sub Quad Length Mismatch: %s != %s' % (
				len(self_sub_quads), len(other_sub_quads)))
			return False

		sub_quads_match = (self_sub_quads == other_sub_quads)
		if not sub_quads_match:
			logging.debug('Sub Quad Mismatch: %s != %s' % (
				self_sub_quads, other_sub_quads))
			return False

		return True

	def _assign_new_quads(self, shards):
		"""Create any quads we'll need all at once. At most one fracture call."""
		# Positions of quads we need to allocate our rect which we don't have
		needed = [x for x in range(len(shards)) if shards[x] and not self.quads[x]]
		if needed:
			new_quads = self.rect.fracture(self.rect.center)
			for pos in needed:
				self.quads[pos] = VerificationQuad(new_quads[pos], self)
				logging.debug("Generating new %s" % self.quads[pos])

class VerificationBlock(blocks.Block):
	def __init__(self, block_id, *args, **kwargs):
		self.block_id = block_id
		super(VerificationBlock, self).__init__(*args, **kwargs)

	def __eq__(self, other):
		return self.block_id == other.block_id

def test_single_layer():
	tree = VerificationQuad(Rect(0, 0, 2, 2))
	block = VerificationBlock('upper_left', Rect(0, 0, 1, 1))
	tree.charge(block)

	verification_tree = VerificationQuad(Rect(0, 0, 2, 2))
	verification_tree.quads[0] = VerificationQuad(Rect(0, 0, 1, 1))
	verification_tree.quads[0].charges.add(VerificationBlock('upper_left', Rect(0, 0, 1, 1)))

	assert tree == verification_tree

def test_double_layer():
	tree = VerificationQuad(Rect(0, 0, 4, 4))
	block = VerificationBlock('b1', Rect(0, 0, 2, 2))
	tree.charge(block)

	block = VerificationBlock('b2', Rect(1, 1, 2, 2))
	tree.charge(block)

	block = VerificationBlock('b3', Rect(2, 2, 2, 2))
	tree.charge(block)


	b1 = VerificationBlock('b1', Rect(0, 0, 2, 2))
	b2 = VerificationBlock('b2', Rect(1, 1, 2, 2))
	b3 = VerificationBlock('b3', Rect(2, 2, 2, 2))
	verification_tree = VerificationQuad(Rect(0, 0, 4, 4))
	verification_tree.quads[0] = VerificationQuad(Rect(0, 0, 2, 2))
	verification_tree.quads[0].charges.add(b1)
	verification_tree.quads[0].quads[2] = VerificationQuad(Rect(1, 1, 1, 1))
	verification_tree.quads[0].quads[2].charges.add(b2)

	verification_tree.quads[1] = VerificationQuad(Rect(2, 0, 2, 2))
	verification_tree.quads[1].quads[3] = VerificationQuad(Rect(2, 1, 1, 1))
	verification_tree.quads[1].quads[3].charges.add(b2)

	verification_tree.quads[2] = VerificationQuad(Rect(2, 2, 2, 2))
	verification_tree.quads[2].charges.add(b3)
	verification_tree.quads[2].quads[0] = VerificationQuad(Rect(2, 2, 1, 1))
	verification_tree.quads[2].quads[0].charges.add(b2)

	verification_tree.quads[3] = VerificationQuad(Rect(0, 2, 2, 2))
	verification_tree.quads[3].quads[1] = VerificationQuad(Rect(1, 2, 1, 1))
	verification_tree.quads[3].quads[1].charges.add(b2)

	assert tree == verification_tree
