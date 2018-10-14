# -*- coding: utf-8 -*-

"""
An basic agent to play the Hanabi game.
"""

import random
from typing import List
from py_hanabi.commands.command import Command
from py_hanabi.commands.command_discard import CommandDiscard
from py_hanabi.commands.command_draw import CommandDraw
from py_hanabi.commands.command_play import CommandPlay
from py_hanabi import analyzer
from py_hanabi.analyzer import generate_observed_matrix
from py_hanabi.card import Card
from py_hanabi.card_matrix import CardMatrix
from py_hanabi.state import State

__author__ = "Jakrin Juangbhanich"
__email__ = "juangbhanich.k@gmail.com"


class Agent:
    def __init__(self, player_index: int):

        self.name: str = "Agent"
        self.player_index: int = player_index

    def hand(self, state: State) -> List[Card]:
        """ Get the agent's hand for this state. """
        return state.get_player_hand(self.player_index)

    def play_command(self, state: State) -> List[Command]:
        """ Analyze the state and return a command to execute. """

        # Set the state dirty so that it resets all of its values.
        hand = state.get_player_hand(self.player_index)
        matrices = self._generate_card_matrix(state)

        # Voluntary play a card.
        card_play = sorted(matrices, key=lambda x: x.rating_play, reverse=True)[0]
        if card_play.rating_play >= 0.99:
            card = hand[card_play.hand_index]
            play_command = CommandPlay(self.player_index, card_play.hand_index, state.is_card_playable(card))
            return self._execute_and_draw(state, play_command)

        # Voluntary discard a card.
        card_discard = sorted(matrices, key=lambda x: x.rating_discard, reverse=True)[0]
        discard_command = CommandDiscard(self.player_index, card_discard.hand_index, not state.hint_token_capped)
        if card_discard.rating_discard >= 0.99:
            return self._execute_and_draw(state, discard_command)

        # Give a hint to another player.
        if state.hint_tokens > 0:
            hints = analyzer.get_valid_hint_commands(state, self.player_index)
            return [random.choice(hints)]

        # No good options, forced to discard.
        return self._execute_and_draw(state, discard_command)

    # ===================================================================================================
    # Support Functions.
    # ===================================================================================================

    def _execute_and_draw(self, state: State, command: Command):
        """ Draw a card after this command, if the deck is not empty. """
        commands: List[Command] = [command]
        if state.number_of_cards_in_deck > 0:
            commands.append(CommandDraw(self.player_index))
        return commands

    def _generate_card_matrix(self, state: State):
        """ Generate a matrix of probability for each card in hand. """

        matrices: List[CardMatrix] = []
        hand: List[Card] = state.get_player_hand(self.player_index)

        # This is what we can already observe. Pre-generate this to save time.
        observed_matrix = generate_observed_matrix(state, self.player_index)

        for i, card in enumerate(hand):

            # Create a new matrix based on all the information that we know.
            matrix = analyzer.get_card_matrix(
                state, self.player_index, card.observed_color, card.observed_number,
                card.not_color, card.not_number, observed_matrix=observed_matrix)

            # Bind it to this hand index.
            matrix.hand_index = i

            matrices.append(matrix)
        return matrices

