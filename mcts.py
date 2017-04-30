import time
import random
import math

import plotly.offline as py
import plotly.graph_objs as go

from fireplace.utils import play_turn
from hearthstone.enums import PlayState
from fireplace.exceptions import GameOver
from hearthstate import HearthState
from utils import random_play

import networkx as nx
import pydotplus
from networkx.drawing.nx_pydot import graphviz_layout

import plotly.graph_objs as go


def plot_graph(G):
	pos = graphviz_layout(G, prog='dot')

	edge_trace = go.Scatter(
		x=[],
		y=[],
		line=go.Line(width=0.5, color='#888'),
		hoverinfo='none',
		mode='lines')

	my_annotations = []

	for edge in G.edges():
		x0, y0 = pos[edge[0]]
		x1, y1 = pos[edge[1]]
		edge_trace['x'] += [x0, x1, None]
		edge_trace['y'] += [y0, y1, None]
		my_annotations.append(
			dict(
				x=(x0 + x1) / 2,
				y=(y0 + y1) / 2,
				xref='x',
				yref='y',
				text='{}'.format(G.get_edge_data(edge[0], edge[1])['action']),
				showarrow=False,
				arrowhead=2,
				ax=0,
				ay=0
			)
		)

	node_trace = go.Scatter(
		x=[],
		y=[],
		text=[],
		mode='markers',
		hoverinfo='text',
		marker=go.Marker(
			showscale=False,
			# colorscale options
			# 'Greys' | 'Greens' | 'Bluered' | 'Hot' | 'Picnic' | 'Portland' |
			# Jet' | 'RdBu' | 'Blackbody' | 'Earth' | 'Electric' | 'YIOrRd' | 'YIGnBu'
			colorscale='YIGnBu',
			reversescale=True,
			color=[],
			size=10,
			colorbar=dict(
				thickness=15,
				title='Node Connections',
				xanchor='left',
				titleside='right'
			),
			line=dict(width=2)))

	for node in G.nodes():
		x, y = pos[node]
		node_trace['x'].append(x)
		node_trace['y'].append(y)

		node_info = str(node)

		node_trace['text'].append(node_info)

	fig = go.Figure(data=go.Data([edge_trace, node_trace]),
					layout=go.Layout(
						title='<br>Network graph made with Python',
						titlefont=dict(size=16),
						showlegend=False,
						width=650,
						height=650,
						hovermode='closest',
						margin=dict(b=20, l=5, r=5, t=40),
						annotations=my_annotations,
						xaxis=go.XAxis(showgrid=False, zeroline=False, showticklabels=False),
						yaxis=go.YAxis(showgrid=False, zeroline=False, showticklabels=False)))
	return fig


class Node:
	def __init__(self, state):

		self.root = None

		self.move = None
		self.visits = 0
		self.reward = 0
		self.parent = None
		self.children = []

		self.state = state

		self.available_moves = set(state.get_moves())
		self.tried_moves = set()

		self.is_terminal = False

	def not_expanded(self):
		return len(self.available_moves - self.tried_moves) > 0

	def non_terminal(self):
		return not self.is_terminal

	def expand(self):
		unchecked_moves = self.available_moves - self.tried_moves

		move = random.sample(unchecked_moves, 1)[0]

		u_new = self.add_child(move)

		return u_new

	def add_child(self, move):

		new_state = self.state.clone()

		new_is_terminal = False
		try:
			new_state.do_move(move)
		except GameOver:
			new_is_terminal = True

		u_new = Node(new_state)

		u_new.is_terminal = new_is_terminal

		u_new.parent = self
		u_new.move = move
		u_new.root = self.root

		self.tried_moves.add(move)
		self.children.append(u_new)

		return u_new

	def best_child(self, c=2):

		ucb1 = lambda u: u.reward / u.visits + c * math.sqrt(math.log(self.root.visits / u.visits))
		best = max(self.children, key=ucb1)

		return best


def uct_search(state: HearthState, timeout=20):
	graph = nx.DiGraph()

	root = Node(state)
	root.root = root

	graph.add_node(root)

	future = timeout + time.time()

	while time.time() < future:

		# selection & expansion
		u_next = tree_policy(root)

		if u_next not in graph:
			graph.add_node(u_next)
			graph.add_edge(u_next.parent, u_next, action=str(u_next.move))

		# simulation
		delta = default_policy(u_next)

		# back propagation
		backup(u_next, delta)

	return root


def backup(u: Node, delta: float):
	while u is not None:
		u.visits += 1
		u.reward += delta
		u = u.parent


def tree_policy(u: Node):
	while u.non_terminal():
		if u.not_expanded():
			return u.expand()
		else:
			u = u.best_child()
	return u


def default_policy(u: Node):
	my_name = u.root.state.game.players[0].name

	if u.non_terminal():
		new_state = u.state.clone()
		try:
			while True:
				random_play(new_state.game)
		except GameOver:
			pass
	else:
		new_state = u.state

	if new_state.game.players[0].name == my_name:
		if new_state.game.players[0].playstate == PlayState.WON:
			return 1
		else:
			return 0
	else:
		if new_state.game.players[1].playstate == PlayState.WON:
			return 1
		else:
			return 0
