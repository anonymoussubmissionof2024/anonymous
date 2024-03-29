# This is for the TSTF setting
# Install required packages.
# !pip install -q torch-scatter==latest+cu101 -f https://pytorch-geometric.com/whl/torch-1.7.0.html
# !pip install -q torch-sparse==latest+cu101 -f https://pytorch-geometric.com/whl/torch-1.7.0.html
# !pip install -q git+https://github.com/rusty1s/pytorch_geometric.git

"""
# Train on subgraph and Test on Full graph. Thus TSTF
"""

import os.path as osp
import pdb

import torch
import torch.nn.functional as F
from torch_geometric.datasets import Planetoid, Reddit, Flickr
from torch_geometric.nn import GCNConv, SAGEConv, SGConv, GATConv
from tqdm import tqdm
from torch_geometric.datasets import Coauthor
import networkx as nx

import time
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import os
import torch.nn as nn
from torch_geometric.data import NeighborSampler

from torch_geometric.utils import subgraph
from torch_geometric.data import Data
import random
import sys

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    auc,
    roc_curve,
    roc_auc_score,
    f1_score,
)

# if torch.cuda.is_available():
#     torch.cuda.set_device(3)  # change this cos sometimes port 0 is full

num_of_runs = 2  # 11  # this runs the program 10 times


class MIA:
    def __init__(
        self,
        args=None,
        posterior=None,
        node_removes=None,
        train_indices=None,
        test_indices=None,
    ) -> None:
        self.args = args
        # self.args = {
        #     "dataset_name": "cora",
        #     "partition_method": "a",
        #     "aggregator": "a",
        #     "ratio_unlearned": 0.1,
        # }
        data_type = self.args["dataset_name"]
        self.posterior = posterior

        self.posterior = torch.exp(self.posterior)
        self.node_removes = node_removes
        self.train_indices = train_indices
        self.test_indices = test_indices

        # data_type = "Cora"  # cora, citeseer, pubmed, cs, physics
        # self.posterior = np.random.rand(2708, 7)
        # self.node_removes = np.arange(100)
        # self.train_indices = np.arange(0, 2100)
        # self.test_indices = np.arange(2100, 2708)
        # data_type = "cora"

        for which_run in range(1, num_of_runs):
            random_data = os.urandom(4)

            rand_state = int.from_bytes(random_data, byteorder="big")
            # print("rand_state", rand_state)
            torch.manual_seed(rand_state)
            random.seed(rand_state)
            np.random.seed(seed=rand_state)

            start_time = time.time()

            # we run each data_type e.g cora against all model type

            """
            Set parameters here ===================================================================================?????????
            """

            model_type = "SGC"  # GCN, GAT, SAGE, SGC
            # data_type = "Cora"  # CiteSeer, Cora, PubMed, Flickr, Reddit

            mode = "TSTF"  # train on subgraph, test on full grah

            save_shadow_OutTrain = (
                "mia/pro_data/posteriorsShadowOut_"
                + self.args["partition_method"]
                + "_"
                + self.args["aggregator"]
                + "_"
                + str(self.args["ratio_unlearned"])
                + "_"
                + mode
                + "_"
                + data_type
                + "_"
                + model_type
                + ".txt"
            )
            save_shadow_InTrain = (
                "mia/pro_data/posteriorsShadowTrain_"
                + self.args["partition_method"]
                + "_"
                + self.args["aggregator"]
                + "_"
                + str(self.args["ratio_unlearned"])
                + "_"
                + mode
                + "_"
                + data_type
                + "_"
                + model_type
                + ".txt"
            )
            save_target_OutTrain = (
                "mia/pro_data/posteriorsTargetOut_"
                + self.args["partition_method"]
                + "_"
                + self.args["aggregator"]
                + "_"
                + str(self.args["ratio_unlearned"])
                + "_"
                + mode
                + "_"
                + data_type
                + "_"
                + model_type
                + ".txt"
            )
            save_target_InTrain = (
                "mia/pro_data/posteriorsTargetTrain_"
                + self.args["partition_method"]
                + "_"
                + self.args["aggregator"]
                + "_"
                + str(self.args["ratio_unlearned"])
                + "_"
                + mode
                + "_"
                + data_type
                + "_"
                + model_type
                + ".txt"
            )

            save_correct_incorrect_homophily_prediction = (
                "mia/pro_data/correct_incorrect_homo_pred"
                + self.args["partition_method"]
                + "_"
                + self.args["aggregator"]
                + "_"
                + str(self.args["ratio_unlearned"])
                + "_"
                + mode
                + "_"
                + data_type
                + "_"
                + model_type
                + ".txt"
            )
            save_global_true_homophily = (
                "true_homophily" + mode + "_" + data_type + "_" + model_type + ".txt"
            )
            save_global_pred_homophily = (
                "pred_homophily" + mode + "_" + data_type + "_" + model_type + ".txt"
            )

            save_target_InTrain_nodes_neigbors = (
                "mia/pro_data/nodesNeigborsTargetTrain_"
                + self.args["partition_method"]
                + "_"
                + self.args["aggregator"]
                + "_"
                + str(self.args["ratio_unlearned"])
                + "_"
                + mode
                + "_"
                + data_type
                + "_"
                + model_type
                + ".npy"
            )
            save_target_OutTrain_nodes_neigbors = (
                "mia/pro_data/nodesNeigborsTargetOut_"
                + self.args["partition_method"]
                + "_"
                + self.args["aggregator"]
                + "_"
                + str(self.args["ratio_unlearned"])
                + "_"
                + mode
                + "_"
                + data_type
                + "_"
                + model_type
                + ".npy"
            )

            result_file = open(
                "mia/result/resultfile_"
                + self.args["partition_method"]
                + "_"
                + self.args["aggregator"]
                + "_"
                + str(self.args["ratio_unlearned"])
                + "_"
                + mode
                + "_"
                + model_type
                + ".txt",
                "a",
            )

            """
            ######################################## Data ##############################################
            """
            if data_type == "Reddit":
                ###################################### Reddit ##################################

                # path = osp.join(osp.dirname(osp.realpath(__file__)), '..', 'data', 'Reddit')
                path = "./data/Reddit"
                dataset = Reddit(path)
                # data = dataset[0]
                # print("len(dataset)", len(dataset)) # Reddit dataset consists of 1 graph
                # print("data", data) # Data(edge_index=[2, 114615892], test_mask=[232965], train_mask=[232965], val_mask=[232965], x=[232965, 602], y=[232965])
                # print("Total Num of nodes in dataset", data.num_nodes) # 232965
                # print("Total Num of edges in dataset", data.num_edges) # 114615892
                # print("Total Num of node features in dataset", data.num_node_features) # 602
                # print("Total Num of features in dataset", dataset.num_features) # same as node features # 602
                # print("Num classes", dataset.num_classes) #41

                # Reduced this cos it's taking too long to create subgraph
                num_train_Train_per_class = 500  # 1000
                num_train_Shadow_per_class = 500  # 1000
                num_test_Target = 20500  # 41000
                num_test_Shadow = 20500  # 41000

            elif data_type == "Flickr":
                ###################################### Flickr ##################################

                path = "./data/Flickr"
                dataset = Flickr(path)
                data = dataset[0]
                # print("len(dataset)", len(dataset))  # Flikr dataset consists of 1 graph
                # print("data",
                #       data)  # Data(edge_index=[2, 899756], test_mask=[89250], train_mask=[89250], val_mask=[89250], x=[89250, 500], y=[89250])
                # print("Total Num of nodes in dataset", data.num_nodes)  # 89250
                # print("Total Num of edges in dataset", data.num_edges)  # 899756
                # print("Total Num of node features in dataset", data.num_node_features)  # 500
                # print("Total Num of features in dataset", dataset.num_features)  # same as node features # 500
                # print("Num classes", dataset.num_classes)  # 7

                num_train_Train_per_class = (
                    1500  # cos min of all classes only have 3k nodes
                )
                num_train_Shadow_per_class = 1500
                num_test_Target = 10500
                num_test_Shadow = 10500

            elif data_type == "cora":
                ###################################### Cora ##################################

                dataset = Planetoid(
                    root="./data/Cora", name="Cora", split="random"
                )  # set test to 1320 to match train
                num_train_Train_per_class = 90  # 180
                num_train_Shadow_per_class = 90
                num_test_Target = 630
                num_test_Shadow = 630

            elif data_type == "citeseer":
                ###################################### CiteSeer ##################################

                dataset = Planetoid(
                    root="./data/CiteSeer", name="CiteSeer", split="random"
                )
                num_train_Train_per_class = 100
                num_train_Shadow_per_class = 100
                num_test_Target = 600
                num_test_Shadow = 600

            elif data_type == "pubmed":
                ###################################### Reddit ##################################

                dataset = Planetoid(root="./data/PubMed", name="PubMed", split="random")

                num_train_Train_per_class = 1500
                num_train_Shadow_per_class = 1500
                num_test_Target = 4500
                num_test_Shadow = 4500

            elif data_type == "Coauthor_CS":
                dataset = Coauthor("./data/Coauthor_CS", name="CS")

                num_train_Train_per_class = 10
                num_train_Shadow_per_class = 1000
                num_test_Target = 150
                num_test_Shadow = 15000

            elif data_type == "Coauthor_Phys":
                dataset = Coauthor("./data/Coauthor_Physics", name="Physics")

                num_train_Train_per_class = 1000
                num_train_Shadow_per_class = 1000
                num_test_Target = 3000
                num_test_Shadow = 3000

            else:
                print("Error: No data specified")

            data = dataset[0]
            # print("data", data)

            """
            ############################################# Posterior Test ###############################################
            """

            if len(self.test_indices) > len(self.node_removes):
                self.test_indices, random_nodes = random.sample(
                    list(self.test_indices), len(self.node_removes)
                ), random.sample(list(self.test_indices), 270)
                self.train_indices = random.sample(list(self.train_indices), 270)

            self.shadow_positive = self.posterior[self.train_indices]
            self.shadow_negative = self.posterior[random_nodes]
            self.test_indices = np.array(self.test_indices)
            self.test_posterior = self.posterior[self.test_indices]
            self.train_posterior = self.posterior[self.node_removes]
            # self.train_posterior = self.posterior[self.train_indices[200:400]]
            # self.train_posterior = self.posterior[self.train_indices[:100]]
            # self.train_posterior = self.posterior[random]

            """
            ############################################# Target and Shadow Models ###############################################
            """

            class TargetModel(torch.nn.Module):
                def __init__(self, dataset):
                    super(TargetModel, self).__init__()

                    if model_type == "GCN":
                        # GCN
                        self.conv1 = GCNConv(dataset.num_node_features, 256)
                        self.conv2 = GCNConv(256, dataset.num_classes)
                    elif model_type == "SAGE":
                        # GraphSage
                        # self.conv1 = SAGEConv(dataset.num_node_features, 256)
                        # self.conv2 = SAGEConv(256, dataset.num_classes)

                        self.num_layers = 2

                        self.convs = torch.nn.ModuleList()
                        self.convs.append(SAGEConv(dataset.num_node_features, 256))
                        self.convs.append(SAGEConv(256, dataset.num_classes))

                    elif model_type == "SGC":
                        # SGC
                        self.conv1 = SGConv(
                            dataset.num_node_features, 256, K=2, cached=False
                        )
                        self.conv2 = SGConv(256, dataset.num_classes, K=2, cached=False)

                    elif model_type == "GAT":
                        # GAT
                        self.conv1 = GATConv(
                            dataset.num_features, 8, heads=8, dropout=0.1
                        )
                        # On the Pubmed dataset, use heads=8 in conv2.
                        if data_type == "PubMed":
                            self.conv2 = GATConv(
                                8 * 8, dataset.num_classes, heads=8, concat=False
                            )
                            # self.conv2 = GATConv(8 * 8, dataset.num_classes, heads=8, concat=False, dropout=0.1)
                        else:
                            self.conv2 = GATConv(
                                8 * 8, dataset.num_classes, heads=1, concat=False
                            )
                    else:
                        print("Error: No model selected")

                def forward(self, x, edge_index):
                    # print("xxxxxxx", x.size())

                    if model_type == "SAGE":
                        all_node_and_neigbors = []
                        all_nodes = []

                        # the edge_index here is quite different (it is a list cos we will be passing train_loader). edge index is different based on batch data.
                        # Note edge_index here is a bipartite graph. meaning all the edges retured are connected
                        for i, (edge_ind, _, size) in enumerate(edge_index):
                            # print("iiiiiiiiiiiiiiii", i)

                            edges_raw = edge_ind.cpu().numpy()
                            # print("edges_raw", edges_raw)
                            edges = [
                                (x, y) for x, y in zip(edges_raw[0, :], edges_raw[1, :])
                            ]

                            G = nx.Graph()
                            G.add_nodes_from(
                                list(range(data.num_nodes))
                            )  # this is set to num_test_Target cos that's the max no of nodes since num_test_Target = num_nodes_in_each_class x num_class. Changed to data.num_nodes instead of num_test_Target
                            G.add_edges_from(edges)

                            # print("x.size(0) forward", x.size(0))
                            # print("x.size forward", x.size())
                            # getting the neigbors of a particular node
                            for n in range(
                                0, x.size(0)
                            ):  # x.size(0) caters for when u input the full graph. This is cos the only the edge_index for those nodes with connectivity will be returned. So this allows getting other nodes without connection.   for n in set(edges_raw[0,:]):  # take first row info of the adjacency matrix. This will give all nodes in the graph!
                                all_nodes.append(n)  # get all nodes
                                # all_node_and_neigbors[n] = [node for node in G.neighbors(n)]  # set the value of the dict to the corresponding value if it has a neighbor else put empty list
                                all_node_and_neigbors.append(
                                    (n, [node for node in G.neighbors(n)])
                                )
                                # print("n:", n, "neighbors:", [n for n in G.neighbors(n)])  # G.adj[n] # gets the neighbors of a particular n

                            # print("all_node_and_neigbors", all_node_and_neigbors)

                            x_target = x[
                                : size[1]
                            ]  # Target nodes are always placed first.
                            x = self.convs[i]((x, x_target), edge_ind)
                            if i != self.num_layers - 1:
                                x = F.relu(x)
                                # x = F.dropout(x, p=0.5, training=self.training)
                        # print("Final all nodes and neighbors", all_node_and_neigbors)
                        return x.log_softmax(dim=-1), all_node_and_neigbors

                    else:
                        # torch.set_printoptions(threshold=10000)
                        # print("x0", x[0])
                        # print("x1", x[1])
                        # print("x", x.shape)
                        # print("edge_index", edge_index.shape)

                        # Begin edit data for passing node n it's neghbprs
                        edges_raw = edge_index.cpu().numpy()
                        # print("edges_raw", edges_raw)
                        edges = [
                            (x, y) for x, y in zip(edges_raw[0, :], edges_raw[1, :])
                        ]

                        G = nx.Graph()
                        G.add_nodes_from(
                            list(range(data.num_nodes))
                        )  # this is set to num_test_Target cos that's the max no of nodes since num_test_Target = num_nodes_in_each_class x num_class. Changed to data.num_nodes instead of num_test_Target
                        G.add_edges_from(edges)

                        all_node_and_neigbors = []
                        all_nodes = []

                        # print("x.size(0) shadow forward", x.size(0))
                        for n in range(
                            0, x.size(0)
                        ):  # x.size(0) caters for when u input the full graph for for n in set(edges_raw[0,:]):  # take first row info of the adjacency matrix. This will give all nodes in the graph!
                            all_nodes.append(n)  # get all nodes
                            # all_node_and_neigbors[n] = [node for node in G.neighbors(n)]  # set the value of the dict to the corresponding value if it has a neighbor else put empty list
                            all_node_and_neigbors.append(
                                (n, [node for node in G.neighbors(n)])
                            )
                            # print("n:", n, "neighbors:", [n for n in G.neighbors(n)])  # G.adj[n] # gets the neighbors of a particular n

                        # print("all_node_and_neigbors", all_node_and_neigbors)

                        x, edge_index = x, edge_index
                        x = self.conv1(x, edge_index)
                        x = F.relu(x)
                        # x = F.dropout(x, p=0.5, training=self.training)
                        # x = F.normalize(x, p=2, dim=-1)
                        x = self.conv2(x, edge_index)
                        # x = F.relu(x)
                        # x = F.normalize(x, p=2, dim=-1)

                        return F.log_softmax(x, dim=1), all_node_and_neigbors

                def inference(self, x_all):
                    # Compute representations of nodes layer by layer, using *all*
                    # available edges. This leads to faster computation in contrast to
                    # immediately computing the final representations of each batch.

                    for i in range(self.num_layers):
                        xs = []
                        all_node_and_neigbors = []
                        all_nodes = []

                        for batch_size, n_id, adj in all_graph_loader:
                            edge_index, _, size = adj.to(device)

                            x = x_all[n_id].to(device)

                            edges_raw = edge_index.cpu().numpy()
                            # print("edges_raw inference", edges_raw)
                            edges = [
                                (x, y) for x, y in zip(edges_raw[0, :], edges_raw[1, :])
                            ]

                            G = nx.Graph()
                            G.add_nodes_from(
                                list(range(data.num_nodes))
                            )  # this is set to num_test_Target cos that's the max no of nodes since num_test_Target = num_nodes_in_each_class x num_class. Changed to data.num_nodes instead of num_test_Target
                            G.add_edges_from(edges)

                            # print("x.size(0)", x.size(0))
                            # print("x.size inference", x.size())
                            for n in range(
                                0, x.size(0)
                            ):  # x.size(0) caters for when u input the full graph. This is cos the only the edge_index for those nodes with connectivity will be returned. So this allows getting other nodes without connection.   for n in set(edges_raw[0,:]):  # take first row info of the adjacency matrix. This will give all nodes in the graph!
                                all_nodes.append(n)  # get all nodes
                                # all_node_and_neigbors[n] = [node for node in G.neighbors(n)]  # set the value of the dict to the corresponding value if it has a neighbor else put empty list
                                all_node_and_neigbors.append(
                                    (n, [node for node in G.neighbors(n)])
                                )
                                # print("n:", n, "neighbors:", [n for n in G.neighbors(n)])  # G.adj[n] # gets the neighbors of a particular n

                            # print("all_node_and_neigbors inference", all_node_and_neigbors)

                            x_target = x[: size[1]]
                            x = self.convs[i]((x, x_target), edge_index)
                            if i != self.num_layers - 1:
                                x = F.relu(x)
                            xs.append(x.cpu())

                        x_all = torch.cat(xs, dim=0)

                    return F.log_softmax(x_all, dim=1), all_node_and_neigbors

            class ShadowModel(torch.nn.Module):
                def __init__(self, dataset):
                    super(ShadowModel, self).__init__()

                    if model_type == "GCN":
                        # GCN
                        self.conv1 = GCNConv(
                            dataset.num_node_features, 32, add_self_loops=False
                        )
                        self.conv2 = GCNConv(
                            32, dataset.num_classes, add_self_loops=False
                        )
                    elif model_type == "SAGE":
                        # GraphSage
                        # self.conv1 = SAGEConv(dataset.num_node_features, 256)
                        # self.conv2 = SAGEConv(256, dataset.num_classes)

                        self.num_layers = 2

                        self.convs = torch.nn.ModuleList()
                        self.convs.append(SAGEConv(dataset.num_node_features, 16))
                        self.convs.append(SAGEConv(16, dataset.num_classes))

                    elif model_type == "SGC":
                        # SGC
                        self.conv1 = SGConv(
                            dataset.num_node_features, 256, K=2, cached=False
                        )
                        self.conv2 = SGConv(256, dataset.num_classes, K=2, cached=False)

                    elif model_type == "GAT":
                        # GAT
                        self.conv1 = GATConv(
                            dataset.num_features, 8, heads=8, dropout=0.1
                        )
                        # On the Pubmed dataset, use heads=8 in conv2.
                        if data_type == "PubMed":
                            self.conv2 = GATConv(
                                8 * 8, dataset.num_classes, heads=8, concat=False
                            )
                            # self.conv2 = GATConv(8 * 8, dataset.num_classes, heads=8, concat=False, dropout=0.1)
                        else:
                            self.conv2 = GATConv(
                                8 * 8, dataset.num_classes, heads=1, concat=False
                            )
                    else:
                        print("Error: No model selected")

                def forward(self, x, edge_index):
                    # print("xxxxxxx", x.size())

                    if model_type == "SAGE":
                        all_node_and_neigbors = []
                        all_nodes = []

                        # the edge_index here is quite different (it is a list cos we will be passing train_loader). edge index is different based on batch data.
                        # Note edge_index here is a bipartite graph. meaning all the edges retured are connected
                        for i, (edge_ind, _, size) in enumerate(edge_index):
                            # print("iiiiiiiiiiiiiiii", i)

                            edges_raw = edge_ind.cpu().numpy()
                            # print("edges_raw", edges_raw)
                            edges = [
                                (x, y) for x, y in zip(edges_raw[0, :], edges_raw[1, :])
                            ]

                            G = nx.Graph()
                            G.add_nodes_from(
                                list(range(data.num_nodes))
                            )  # this is set to num_test_Shadow cos that's the max no of nodes since num_test_Shadow = num_nodes_in_each_class x num_class. Changed to data.num_nodes instead of num_test_Shadow
                            G.add_edges_from(edges)

                            # print("x.size(0) shadow forward", x.size(0))
                            # print("x.size", x.size())
                            for n in range(
                                0, x.size(0)
                            ):  # x.size(0) caters for when u input the full graph. This is cos the only the edge_index for those nodes with connectivity will be returned. So this allows getting other nodes without connection.   for n in set(edges_raw[0,:]):  # take first row info of the adjacency matrix. This will give all nodes in the graph!
                                all_nodes.append(n)  # get all nodes
                                # all_node_and_neigbors[n] = [node for node in G.neighbors(n)]  # set the value of the dict to the corresponding value if it has a neighbor else put empty list
                                all_node_and_neigbors.append(
                                    (n, [node for node in G.neighbors(n)])
                                )
                                # print("n:", n, "neighbors:", [n for n in G.neighbors(n)])  # G.adj[n] # gets the neighbors of a particular n

                            # print("all_node_and_neigbors", all_node_and_neigbors)

                            x_shadow = x[
                                : size[1]
                            ]  # Shadow nodes are always placed first.
                            x = self.convs[i]((x, x_shadow), edge_ind)
                            if i != self.num_layers - 1:
                                x = F.relu(x)
                                x = F.dropout(x, p=0.5, training=self.training)
                        # print("Final all nodes and neighbors", all_node_and_neigbors)
                        return x.log_softmax(dim=-1), all_node_and_neigbors

                    else:
                        # Begin edit data for passing node n it's neghbprs
                        edges_raw = edge_index.cpu().numpy()
                        # print("edges_raw", edges_raw)
                        edges = [
                            (x, y) for x, y in zip(edges_raw[0, :], edges_raw[1, :])
                        ]

                        G = nx.Graph()
                        G.add_nodes_from(
                            list(range(data.num_nodes))
                        )  # this is set to num_test_Shadow cos that's the max no of nodes since num_test_Shadow = num_nodes_in_each_class x num_class. Changed to data.num_nodes instead of num_test_Shadow
                        G.add_edges_from(edges)

                        all_node_and_neigbors = []
                        all_nodes = []

                        # print("x.size(0)", x.size(0))
                        for n in range(
                            0, x.size(0)
                        ):  # x.size(0) caters for when u input the full graph for for n in set(edges_raw[0,:]):  # take first row info of the adjacency matrix. This will give all nodes in the graph!
                            all_nodes.append(n)  # get all nodes
                            # all_node_and_neigbors[n] = [node for node in G.neighbors(n)]  # set the value of the dict to the corresponding value if it has a neighbor else put empty list
                            all_node_and_neigbors.append(
                                (n, [node for node in G.neighbors(n)])
                            )
                            # print("n:", n, "neighbors:", [n for n in G.neighbors(n)])  # G.adj[n] # gets the neighbors of a particular n

                        # Therefore no need to save nodes. Just loop through

                        # print("all_node_and_neigbors", all_node_and_neigbors)

                        x, edge_index = x, edge_index
                        x = self.conv1(x, edge_index)
                        x = F.relu(x)
                        x = F.dropout(x, training=self.training)
                        # x = F.normalize(x, p=2, dim=-1)
                        x = self.conv2(x, edge_index)
                        # x = F.relu(x)
                        # x = F.normalize(x, p=2, dim=-1)

                        return F.log_softmax(x, dim=1), all_node_and_neigbors

                def inference(self, x_all):
                    # Compute representations of nodes layer by layer, using *all*
                    # available edges. This leads to faster computation in contrast to
                    # immediately computing the final representations of each batch.

                    for i in range(self.num_layers):
                        xs = []
                        all_node_and_neigbors = []
                        all_nodes = []

                        for batch_size, n_id, adj in all_graph_loader:
                            edge_index, _, size = adj.to(device)

                            x = x_all[n_id].to(device)

                            edges_raw = edge_index.cpu().numpy()
                            # print("edges_raw inference", edges_raw)
                            edges = [
                                (x, y) for x, y in zip(edges_raw[0, :], edges_raw[1, :])
                            ]

                            G = nx.Graph()
                            G.add_nodes_from(
                                list(range(data.num_nodes))
                            )  # this is set to num_test_Shadow cos that's the max no of nodes since num_test_Shadow = num_nodes_in_each_class x num_class. Changed to data.num_nodes instead of num_test_Shadow
                            G.add_edges_from(edges)

                            # print("x.size(0)", x.size(0))
                            # print("x.size inference", x.size())
                            for n in range(
                                0, x.size(0)
                            ):  # x.size(0) caters for when u input the full graph. This is cos the only the edge_index for those nodes with connectivity will be returned. So this allows getting other nodes without connection.   for n in set(edges_raw[0,:]):  # take first row info of the adjacency matrix. This will give all nodes in the graph!
                                all_nodes.append(n)  # get all nodes
                                # all_node_and_neigbors[n] = [node for node in G.neighbors(n)]  # set the value of the dict to the corresponding value if it has a neighbor else put empty list
                                all_node_and_neigbors.append(
                                    (n, [node for node in G.neighbors(n)])
                                )
                                # print("n:", n, "neighbors:", [n for n in G.neighbors(n)])  # G.adj[n] # gets the neighbors of a particular n

                            # print("all_node_and_neigbors inference", all_node_and_neigbors)

                            x_shadow = x[: size[1]]
                            x = self.convs[i]((x, x_shadow), edge_index)
                            if i != self.num_layers - 1:
                                x = F.relu(x)
                            xs.append(x.cpu())

                        x_all = torch.cat(xs, dim=0)

                    return F.log_softmax(x_all, dim=1), all_node_and_neigbors

            """
            ##################################### Data Processing Inductive Split ######################################
            """

            def get_inductive_spilt(
                data,
                num_classes,
                num_train_Train_per_class,
                num_train_Shadow_per_class,
                num_test_Target,
                num_test_Shadow,
            ):
                # -----------------------------------------------------------------------
                # target_train, target_out
                # shadow_train, shadow_out
                """
                Randomly choose 'num_train_Train_per_class' and 'num_train_Shadow_per_class' per classes for training Target and shadow models respectively
                Random choose 'num_test_Target' and 'num_test_Shadow' for testing (out data) Target and shadow models respectively

                """

                # convert all label to list
                label_idx = data.y.numpy().tolist()
                # print("label_idx", len(label_idx))
                target_train_idx = []
                shadow_train_idx = []
                # for i in range(num_classes):
                #     c = [x for x in range(len(label_idx)) if label_idx[x] == i]
                #     print("c", len(c)) #the min is 180 which is 7th class
                #     sample = random.sample(range(c),num_train_Train_per_class)
                #     target_train_idx.extend(sample)

                for c in range(num_classes):
                    idx = (data.y == c).nonzero().view(-1)
                    sample_train_idx = idx[torch.randperm(idx.size(0))]
                    sample_target_train_idx = sample_train_idx[
                        :num_train_Train_per_class
                    ]
                    target_train_idx.extend(sample_target_train_idx)

                    # print(
                    #     "idx.size(0)", idx.size(0)
                    # )  # this is the total number of data in each class

                    # Ensure they don't over lap
                    # sample_shadow_train_idx = idx[torch.randperm(idx.size(0))[num_train_Train_per_class:num_train_Train_per_class + num_train_Shadow_per_class]]
                    sample_shadow_train_idx = sample_train_idx[
                        num_train_Train_per_class : num_train_Train_per_class
                        + num_train_Shadow_per_class
                    ]
                    shadow_train_idx.extend(sample_shadow_train_idx)

                # print("shadow_train_idx", len(shadow_train_idx))
                # print("Target_train_idx", len(target_train_idx))

                others = [
                    x
                    for x in range(len(label_idx))
                    if x not in set(target_train_idx) and x not in set(shadow_train_idx)
                ]
                # print("others",others)
                # print("done others")
                target_test_idx = random.sample(others, num_test_Target)
                # print("done target test")
                shadow_test = [x for x in others if x not in set(target_test_idx)]
                shadow_test_idx = random.sample(shadow_test, num_test_Shadow)
                # print("done shadow test")

                # print("target_test_idx", target_test_idx)
                # print("shadow_test_idx", shadow_test_idx)

                # ----------set values for mask--------------------------------

                # This is done cos in SAGE, we use the mask to create loader. But in other GNN, we only use it to get the sum of elements
                if model_type == "SAGE":
                    target_train_mask = torch.zeros(data.num_nodes, dtype=torch.bool)
                    for i in target_train_idx:
                        target_train_mask[i] = 1

                    shadow_train_mask = torch.zeros(data.num_nodes, dtype=torch.bool)
                    for i in shadow_train_idx:
                        shadow_train_mask[i] = 1

                else:
                    # Other GNN
                    # Also changed this so as to conform with the shape of others. No, this uncommented one is better
                    target_train_mask = torch.ones(
                        len(target_train_idx), dtype=torch.bool
                    )
                    shadow_train_mask = torch.ones(
                        len(shadow_train_idx), dtype=torch.bool
                    )

                # # Also changed this so as to conform with the shape of others. No, this uncommented one is better
                # target_train_mask = torch.ones(len(target_train_idx), dtype=torch.bool)
                # shadow_train_mask = torch.ones(len(shadow_train_idx), dtype=torch.bool)

                # print("target_train_mask.shape", target_train_mask.shape)

                # ---test-mask---
                target_test_mask = torch.zeros(data.num_nodes, dtype=torch.bool)
                for i in target_test_idx:
                    target_test_mask[i] = 1
                # ---val-mask-----
                shadow_test_mask = torch.zeros(data.num_nodes, dtype=torch.bool)
                for i in shadow_test_idx:
                    shadow_test_mask[i] = 1

                """
                get all nodes and corresponding edge_index information
                """
                # This is for creating subgraphs

                # For target
                target_x_inductive = data.x[target_train_idx]
                target_y_inductive = data.y[target_train_idx]
                target_edge_index_inductive, _ = subgraph(
                    target_train_idx, data.edge_index
                )

                # For shadow
                shadow_x_inductive = data.x[shadow_train_idx]
                shadow_y_inductive = data.y[shadow_train_idx]
                shadow_edge_index_inductive, _ = subgraph(
                    shadow_train_idx, data.edge_index
                )

                """
                in this part use a vertex_map to get a correct target_edge_index_inductive
                """
                # ---*---*---*---*---*---*---*---*---*---*---*---*---*---*---*---*---*---*---*---*---*---*
                """
                get new edge_index information, because some nodes were removed from orginal nodes set. so there
                are some edge_index that will disappear. If we dont do that, it will cause error: out of index 193
                """

                target_vertex_map = {}
                ind = -1
                for i in range(data.num_nodes):
                    if i in target_train_idx:
                        ind += 1
                        target_vertex_map[i] = ind
                for i in range(target_edge_index_inductive.shape[1]):
                    target_edge_index_inductive[0, i] = target_vertex_map[
                        target_edge_index_inductive[0, i].tolist()
                    ]
                    target_edge_index_inductive[1, i] = target_vertex_map[
                        target_edge_index_inductive[1, i].tolist()
                    ]

                shadow_vertex_map = {}
                ind = -1
                for i in range(data.num_nodes):
                    if i in shadow_train_idx:
                        ind += 1
                        shadow_vertex_map[i] = ind
                for i in range(shadow_edge_index_inductive.shape[1]):
                    shadow_edge_index_inductive[0, i] = shadow_vertex_map[
                        shadow_edge_index_inductive[0, i].tolist()
                    ]
                    shadow_edge_index_inductive[1, i] = shadow_vertex_map[
                        shadow_edge_index_inductive[1, i].tolist()
                    ]

                # ---*---*---*---*---*---*---*---*---*---*---*---*---*---*---*---*---*---*---*---*---*---*

                # All graph data
                all_x = data.x
                all_y = data.y
                all_edge_index = data.edge_index

                """
                now we create a New data instances for save the all data with that we do inductive learning tasks
                """
                data = Data(
                    target_x=target_x_inductive,
                    target_edge_index=target_edge_index_inductive,
                    target_y=target_y_inductive,
                    shadow_x=shadow_x_inductive,
                    shadow_edge_index=shadow_edge_index_inductive,
                    shadow_y=shadow_y_inductive,
                    target_train_mask=target_train_mask,
                    shadow_train_mask=shadow_train_mask,
                    all_x=all_x,
                    all_edge_index=all_edge_index,
                    all_y=all_y,
                    target_test_mask=target_test_mask,
                    shadow_test_mask=shadow_test_mask,
                )

                # # flipping the shadow to target and target to shadow
                # data = Data(target_x=shadow_x_inductive,target_edge_index=shadow_edge_index_inductive,target_y=shadow_y_inductive,
                #                 shadow_x=target_x_inductive, shadow_edge_index=target_edge_index_inductive,shadow_y=target_y_inductive,
                #                 target_train_mask=shadow_train_mask,shadow_train_mask=target_train_mask,
                #                 all_x=all_x,all_edge_index=all_edge_index,all_y=all_y,
                #                 target_test_mask=shadow_test_mask, shadow_test_mask=target_test_mask)

                return data

            def get_train_acc(data_new, pred, isTarget=True):
                if isTarget:
                    # Removed train mask cos u r testing on the subgraph only tho
                    # train_acc = pred.eq(data_new.target_y[data_new.target_train_mask]).sum().item() / data_new.target_train_mask.sum().item()
                    train_acc = (
                        pred.eq(data_new.target_y).sum().item()
                        / data_new.target_train_mask.sum().item()
                    )
                else:
                    # train_acc = pred.eq(data_new.target_y[data_new.shadow_train_mask]).sum().item() / data_new.shadow_train_mask.sum().item()
                    train_acc = (
                        pred.eq(data_new.shadow_y).sum().item()
                        / data_new.shadow_train_mask.sum().item()
                    )
                # I changed this so as to get the prediction when u test on the train dataset cos all_y has all y. No this approach is not good. The apporach above is accurate
                # train_acc = pred.eq(data_new.all_y[data_new.target_train_mask]).sum().item() / data_new.target_train_mask.sum().item()
                return train_acc

            def get_test_acc(data_new, pred, isTarget=True):
                if isTarget:
                    test_acc = (
                        pred.eq(data_new.all_y[data_new.target_test_mask]).sum().item()
                        / data_new.target_test_mask.sum().item()
                    )
                else:
                    test_acc = (
                        pred.eq(data_new.all_y[data_new.shadow_test_mask]).sum().item()
                        / data_new.shadow_test_mask.sum().item()
                    )
                return test_acc

            def get_marco_f1(data_new, pred_labels, true_labels, label_list):
                # f1_marco = f1_score(true_labels,pred_labels,label_list,average='macro')
                f1_marco = f1_score(true_labels, pred_labels, average="macro")
                return f1_marco

            def get_micro_f1(data_new, pred_labels, true_labels, label_list):
                # f1_micro = f1_score(true_labels,pred_labels,label_list,average='micro')
                f1_micro = f1_score(true_labels, pred_labels, average="micro")
                return f1_micro

            """
            ########################## End Data Processing Inductive Split ###########################
            """

            """ Data initalization """

            # --- create labels_list---
            label_list = [x for x in range(dataset.num_classes)]

            # convert all label to list
            label_idx = data.y.numpy().tolist()

            data_new = get_inductive_spilt(
                data,
                dataset.num_classes,
                num_train_Train_per_class,
                num_train_Shadow_per_class,
                num_test_Target,
                num_test_Shadow,
            )

            # print("data", data)
            # print("data new", data_new)
            # print("data_new.shadow_test_mask.sum()", data_new.shadow_test_mask.sum())
            # print("data_new.target_test_mask.sum()", data_new.target_test_mask.sum())

            # print(dataset.num_classes)

            bool_tensor = torch.ones(num_test_Target, dtype=torch.bool)

            target_train_loader = NeighborSampler(
                data_new.target_edge_index,
                node_idx=bool_tensor,
                sizes=[25, 10],
                num_nodes=num_test_Target,
                batch_size=64,
                shuffle=False,
            )  # solution: node_idx to none since we wanna consider all nodes in the subgraph. Also num_test_Target is used cos its the total of nodes
            # print("data_new.target_edge_index", data_new.target_edge_index.shape)
            # print("data_new.target_x", data_new.target_x.shape)
            # print("data_new.target_train_mask", data_new.target_train_mask)

            shadow_train_loader = NeighborSampler(
                data_new.shadow_edge_index,
                node_idx=bool_tensor,
                sizes=[25, 10],
                num_nodes=num_test_Shadow,
                batch_size=64,
                shuffle=False,
            )

            # This is left cos we are training on the full graph. i.e TSTF
            all_graph_loader = NeighborSampler(
                data_new.all_edge_index,
                node_idx=None,
                sizes=[-1],
                batch_size=1024,
                num_nodes=data.num_nodes,
                shuffle=False,
            )

            """ Model initialization """

            target_model = TargetModel(dataset)
            shadow_model = ShadowModel(
                dataset
            )  # Defining it as TargetModel(dataset) still produces the same result. I explicitly redefined each model for clarity

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            data_new = data_new.to(device)

            target_model = target_model.to(device)

            # # To reset the model to default
            # for name, module in target_model.named_children():
            #     print('resetting ', name)
            #     module.reset_parameters()

            shadow_model = shadow_model.to(device)

            # print("model", target_model)
            if model_type == "SAGE":
                # better attack but slighly less test acc
                if data_type == "PubMed":
                    target_optimizer = torch.optim.Adam(
                        target_model.parameters(), lr=0.0001
                    )
                    shadow_optimizer = torch.optim.Adam(
                        shadow_model.parameters(), lr=0.0001
                    )  # 01
                else:
                    target_optimizer = torch.optim.Adam(
                        target_model.parameters(), lr=0.001
                    )
                    shadow_optimizer = torch.optim.Adam(
                        shadow_model.parameters(), lr=0.001
                    )  # 01
            else:
                target_optimizer = torch.optim.Adam(
                    target_model.parameters(), lr=0.0001
                )
                shadow_optimizer = torch.optim.Adam(
                    shadow_model.parameters(), lr=0.0001
                )

            """
            Train and Test function for model
            """

            # --*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*
            # #----------------------------- TRAIN FUCNTION---------------------------
            def train(model, optimizer, isTarget=True):
                model.train()
                optimizer.zero_grad()
                if isTarget:
                    out, nodes_and_neighbors = model(
                        data_new.target_x, data_new.target_edge_index
                    )
                    loss = F.nll_loss(out, data_new.target_y)
                else:
                    out, nodes_and_neighbors = model(
                        data_new.shadow_x, data_new.shadow_edge_index
                    )
                    loss = F.nll_loss(out, data_new.shadow_y)

                pred = torch.exp(out)
                # print("pred", pred)

                loss.backward()
                optimizer.step()

                # approximate accuracy
                if isTarget:
                    train_loss = loss.item() / int(data_new.target_train_mask.sum())
                    total_correct = int(
                        pred.argmax(dim=-1).eq(data_new.target_y).sum()
                    ) / int(data_new.target_train_mask.sum())
                    # np.savetxt("save_Target_Train", pred.cpu().detach().numpy())
                else:
                    train_loss = loss.item() / int(data_new.shadow_train_mask.sum())
                    total_correct = int(
                        pred.argmax(dim=-1).eq(data_new.shadow_y).sum()
                    ) / int(data_new.shadow_train_mask.sum())
                    # np.savetxt("save_Shadow_Train", pred.cpu().detach().numpy())
                return total_correct, train_loss

            def train_SAGE(model, optimizer, isTarget=True):
                # print("================ Begin SAGE Train ==================")
                model.train()

                if isTarget:
                    total_loss = total_correct = 0
                    for batch_size, n_id, adjs in target_train_loader:
                        # `adjs` holds a list of `(edge_index, e_id, size)` tuples.
                        adjs = [adj.to(device) for adj in adjs]
                        # print("adjs", adjs)

                        optimizer.zero_grad()
                        out, nodes_and_neighbors = model(data_new.target_x[n_id], adjs)
                        # print("out traaaaain", out.shape)
                        loss = F.nll_loss(out, data_new.target_y[n_id[:batch_size]])
                        loss.backward()
                        optimizer.step()

                        total_loss += float(loss)
                        total_correct += int(
                            out.argmax(dim=-1)
                            .eq(data_new.target_y[n_id[:batch_size]])
                            .sum()
                        )

                    loss = total_loss / len(target_train_loader)
                    approx_acc = total_correct / int(data_new.target_train_mask.sum())

                else:
                    # Shadow training
                    total_loss = total_correct = 0
                    for batch_size, n_id, adjs in shadow_train_loader:
                        # `adjs` holds a list of `(edge_index, e_id, size)` tuples.
                        adjs = [adj.to(device) for adj in adjs]
                        # print("adjs", adjs)

                        optimizer.zero_grad()
                        out, nodes_and_neighbors = model(data_new.shadow_x[n_id], adjs)
                        # print("out traaaaain shadow", out.shape)
                        loss = F.nll_loss(out, data_new.shadow_y[n_id[:batch_size]])
                        loss.backward()
                        optimizer.step()

                        total_loss += float(loss)
                        total_correct += int(
                            out.argmax(dim=-1)
                            .eq(data_new.shadow_y[n_id[:batch_size]])
                            .sum()
                        )

                    loss = total_loss / len(shadow_train_loader)
                    approx_acc = total_correct / int(data_new.shadow_train_mask.sum())

                # print("================ End SAGE Train ==================")
                return approx_acc, loss

            # -----------------------------------------------------------------------------------------------
            # -----*-----*-----*-----*-----*-----*-----*-----*-----*-----*-----*-----*-----*-----*-----*-----*
            # -------------------------------- TEST FUNCTION -----------------------------------------
            def test(model, isTarget=True):
                model.eval()
                # Also changed this to give true test using full graph. This will give the true train result--No it wont. See comment below

                # This is a better n accurate approach
                if isTarget:
                    """InTrain Target"""
                    # Removed train mask cos u r training on the subgraph not the full graph. Therefore, train mask is useless
                    # pred_Intrain = model(data_new.target_x,data_new.target_edge_index)[data_new.target_train_mask].max(1)[1]
                    pred, nodes_and_neighbors = model(
                        data_new.target_x, data_new.target_edge_index
                    )
                    pred_Intrain = pred.max(1)[1].to(device)
                    # Actual probabilities
                    # pred_Intrain_ps = torch.exp(model(data_new.target_x,data_new.target_edge_index)[data_new.target_train_mask])
                    pred_Intrain_ps = torch.exp(pred)
                    np.savetxt(
                        save_target_InTrain, pred_Intrain_ps.cpu().detach().numpy()
                    )

                    np.save(
                        save_target_InTrain_nodes_neigbors,
                        np.array(nodes_and_neighbors, dtype=object),
                    )
                    # print("nodes_and_neighborsnodes_and_neighbors", nodes_and_neighbors) # 630

                    # print("End InTrain for target")

                    """OutTrain Target"""
                    # This is where the difference is

                    # preds, nodes_and_neighbors = model(data_new.all_x, data_new.all_edge_index)[data_new.target_test_mask]
                    preds, nodes_and_neighbors = model(
                        data_new.all_x, data_new.all_edge_index
                    )  # [data_new.target_test_mask]
                    nodes_and_neighbors = np.array(nodes_and_neighbors, dtype=object)
                    # print("type(preds)", type(preds), "type(nodes_and_neighbors)", type(nodes_and_neighbors))
                    # print("preds.shape", preds.shape)
                    # print("nodes_and_neighbors.shape", nodes_and_neighbors) # 2708

                    preds = preds[data_new.target_test_mask]
                    # print("baba1")
                    mask = data_new.target_test_mask.gt(
                        0
                    )  # trick to convert to true false for masking nodes_and_neighbors cos its a numpy array
                    mask = mask.cpu().numpy()
                    # print("data_new.target_test_mask", data_new.target_test_mask)
                    # print("mask", mask)
                    # print(nodes_and_neighbors)
                    nodes_and_neighbors = nodes_and_neighbors[mask]
                    # print("baba2")

                    pred_out = preds.max(1)[1].to(device)
                    pred_out_ps = torch.exp(preds)

                    # Increment each node in dict by (num_test_Target) e.g 630 as well as the values for ease of "continuing" the graph since each graph is recreated
                    # This will allow shuffling of posteriors in the attack model not to loose the node info
                    # print("newwwwwwww", nodes_and_neighbors)

                    incremented_nodes_and_neighbors = []  # {}
                    # for i in range(len(nodes_and_neighbors)):
                    #     # print(nodes_and_neighbors[i])  # list
                    #     res = [x + num_test_Target for x in nodes_and_neighbors[i]]
                    #     incremented_nodes_and_neighbors[i+num_test_Target] = res

                    for i in range(len(nodes_and_neighbors)):  # range 630
                        # print("nodes_and_neighbors[i]", nodes_and_neighbors[i])  # list with num_nodes. nodes_and_neighbors[i] [2694 list([431, 2695])]
                        # print(nodes_and_neighbors[i][0])
                        # print(nodes_and_neighbors[i][1])

                        # print("num_test_Target", num_test_Target)

                        res = nodes_and_neighbors[i][
                            1
                        ]  # [x + num_test_Target for x in nodes_and_neighbors[i][1]] #increment from 630 num_test_Target
                        res_0 = nodes_and_neighbors[i][
                            0
                        ]  # nodes_and_neighbors[i][0] + data.num_nodes
                        incremented_nodes_and_neighbors.append((res_0, res))

                    # print("incremented_nodes_and_neighbors", incremented_nodes_and_neighbors)

                    np.save(
                        save_target_OutTrain_nodes_neigbors,
                        np.array(incremented_nodes_and_neighbors, dtype=object),
                    )

                    # Simply the nodes are the last column of the "posterior"
                    nodes = []
                    for i in range(0, len(incremented_nodes_and_neighbors)):
                        # print("len(incremented_nodes_and_neighbors)", len(incremented_nodes_and_neighbors)) # 630
                        # print("incremented_nodes_and_neighbors[i][0]", incremented_nodes_and_neighbors[i][0])
                        nodes.append(incremented_nodes_and_neighbors[i][0])
                    nodes = np.array(nodes)

                    # print("nodesnodes",nodes)
                    preds_and_nodes = np.column_stack(
                        (pred_out_ps.cpu().detach().numpy(), nodes)
                    )
                    # print("preds_and_nodes", preds_and_nodes.shape)
                    np.savetxt(
                        save_target_OutTrain, preds_and_nodes
                    )  # pred_out_ps.cpu().detach().numpy()

                    # print("End OutTrain for target")

                    pred_labels = pred_out.tolist()
                    true_labels = data_new.all_y[data_new.target_test_mask].tolist()

                    # The train accuracy is not on the full graph. It's similar to approx_train_acc
                    train_acc = get_train_acc(data_new, pred_Intrain)
                    # Test n val are on full graph
                    test_acc = get_test_acc(data_new, pred_out)

                else:
                    """InTrain Shadow"""
                    # pred_Intrain = model(data_new.shadow_x, data_new.shadow_edge_index)[data_new.shadow_train_mask].max(1)[1]
                    pred, nodes_and_neighbors = model(
                        data_new.shadow_x, data_new.shadow_edge_index
                    )
                    pred_Intrain = pred.max(1)[1].to(device)
                    # Actual probabilities
                    # pred_Intrain_ps = torch.exp(model(data_new.shadow_x, data_new.shadow_edge_index)[data_new.shadow_train_mask])
                    pred_Intrain_ps = torch.exp(pred)
                    # pred_Intrain_ps = self.shadow_positive
                    np.savetxt(
                        save_shadow_InTrain, pred_Intrain_ps.cpu().detach().numpy()
                    )

                    """OutTrain Shadow"""

                    # preds, nodes_and_neighbors = model(data_new.all_x, data_new.all_edge_index)[data_new.shadow_test_mask]
                    preds, nodes_and_neighbors = model(
                        data_new.all_x, data_new.all_edge_index
                    )  # [data_new.shadow_test_mask]
                    nodes_and_neighbors = np.array(nodes_and_neighbors, dtype=object)
                    # print("type(preds)", type(preds), "type(nodes_and_neighbors)", type(nodes_and_neighbors))
                    # print("preds.shape", preds.shape)
                    # print("nodes_and_neighbors.shape", nodes_and_neighbors.shape)

                    preds = preds[data_new.shadow_test_mask]
                    # print("baba1")
                    mask = data_new.shadow_test_mask.gt(0)  # trick to
                    mask = mask.cpu().numpy()
                    # print("data_new.shadow_test_mask", data_new.shadow_test_mask)
                    # print("mask", mask.shape)
                    # print(nodes_and_neighbors)
                    nodes_and_neighbors = nodes_and_neighbors[mask]
                    # print("baba2")

                    # preds, nodes_and_neighbors = model(data_new.all_x, data_new.all_edge_index)[data_new.shadow_test_mask]
                    pred_out = preds.max(1)[1].to(device)
                    pred_out_ps = torch.exp(preds)
                    # pred_out_ps = self.shadow_negative
                    np.savetxt(save_shadow_OutTrain, pred_out_ps.cpu().detach().numpy())

                    pred_labels = pred_out.tolist()
                    true_labels = data_new.all_y[data_new.shadow_test_mask].tolist()

                    # The train accuracy is not on the full graph. It's similar to approx_train_acc
                    train_acc = get_train_acc(data_new, pred_Intrain, False)
                    # Test n val are on full graph
                    test_acc = get_test_acc(data_new, pred_out, False)

                # pred_Intrain = model(data_new.all_x,data_new.all_edge_index)[data_new.target_train_mask].max(1)[1]
                # # Actual probabilities
                # pred_Intrain_ps = torch.exp(model(data_new.all_x,data_new.all_edge_index)[data_new.target_train_mask])

                # print("posteriors", pred_Intrain)

                # The f1 measures are on test dataset
                f1_marco = get_marco_f1(data_new, pred_labels, true_labels, label_list)
                f1_micro = get_micro_f1(data_new, pred_labels, true_labels, label_list)

                return train_acc, test_acc, f1_marco, f1_micro

            def test_SAGE(model, isTarget=True):
                # print("****************** SAGE test begin *************************")
                model.eval()
                # Also changed this to give true test using full graph. This will give the true train result--No it wont. See comment below

                # This is a better n accurate approach
                if isTarget:
                    """InTrain Target"""
                    # Removed train mask cos u r training on the subgraph not the full graph. Therefore, train mask is useless
                    # pred_Intrain = model(data_new.target_x,data_new.target_edge_index)[data_new.target_train_mask].max(1)[1]

                    pred = []
                    nodes_and_neighbors = []

                    total_target_train_correct = 0

                    for batch_size, n_id, adjs in target_train_loader:
                        # `adjs` holds a list of `(edge_index, e_id, size)` tuples.
                        adjs = [adj.to(device) for adj in adjs]
                        # print("adjs test", adjs)
                        # print("n_id",len(n_id))

                        out, node_and_neigh = model(data_new.target_x[n_id], adjs)
                        out = torch.exp(out)
                        # print("out test", out.shape)
                        pred.append(out.cpu())
                        nodes_and_neighbors.append(node_and_neigh)

                        total_target_train_correct += int(
                            out.argmax(dim=-1)
                            .eq(data_new.target_y[n_id[:batch_size]])
                            .sum()
                        )

                    target_train_acc = total_target_train_correct / int(
                        data_new.target_train_mask.sum()
                    )  # similar to get_train_acc()
                    # print("target_train_acc", target_train_acc)

                    # Need to concat all preds cos it's per batch
                    pred_all_inTrain = torch.cat(pred, dim=0)

                    # pred, nodes_and_neighbors = model(data_new.target_x,data_new.target_edge_index)
                    pred_Intrain = pred_all_inTrain.max(1)[1].to(device)
                    # # Actual probabilities
                    # # pred_Intrain_ps = torch.exp(model(data_new.target_x,data_new.target_edge_index)[data_new.target_train_mask])
                    pred_Intrain_ps = pred_all_inTrain  # torch.exp(pred)
                    np.savetxt(
                        save_target_InTrain, pred_Intrain_ps.cpu().detach().numpy()
                    )
                    #
                    np.save(save_target_InTrain_nodes_neigbors, nodes_and_neighbors)
                    # print("nodes_and_neighborsnodes_and_neighbors", nodes_and_neighbors) # 630

                    # print("End InTrain for target")

                    """OutTrain Target"""
                    # This is where the difference is
                    out, nodes_and_neighbors = model.inference(data_new.all_x)
                    # print("out OutTrain Target", out.shape)

                    y_true = data_new.all_y.cpu().unsqueeze(-1)
                    y_pred = out.argmax(dim=-1, keepdim=True)

                    # print(y_pred[data_new.target_train_mask])

                    # results = []
                    # for mask in [data_new.target_train_mask, data_new.target_test_mask]:
                    #     results += [int(y_pred[mask].eq(y_true[mask]).sum()) / int(mask.sum())]

                    # train_acc = int(y_pred[data_new.target_train_mask].eq(y_true[data_new.target_train_mask]).sum()) / int(data_new.target_train_mask.sum())
                    # test_acc = int(y_pred[data_new.target_test_mask].eq(y_true[data_new.target_test_mask]).sum()) / int(data_new.target_test_mask.sum())

                    # # preds, nodes_and_neighbors = model(data_new.all_x, data_new.all_edge_index)[data_new.target_test_mask]
                    # preds, nodes_and_neighbors = model(data_new.all_x, data_new.all_edge_index)#[data_new.target_test_mask]
                    nodes_and_neighbors = np.array(nodes_and_neighbors)
                    # print("type(preds)", type(preds), "type(nodes_and_neighbors)", type(nodes_and_neighbors))
                    # print("preds.shape", preds.shape)
                    # print("nodes_and_neighbors.shape", nodes_and_neighbors.shape) # 2708
                    #
                    preds = out[data_new.target_test_mask]
                    # print("predsssssssssssssssss", torch.exp(preds).shape)
                    mask = data_new.target_test_mask.gt(
                        0
                    )  # trick to convert to true false for masking nodes_and_neighbors cos its a numpy array
                    mask = mask.cpu().numpy()
                    # print("data_new.target_test_mask", data_new.target_test_mask)
                    # print("mask", mask)
                    # print("nodes_and_neighborsnodes_and_neighbors", nodes_and_neighbors)

                    nodes_and_neighbors = nodes_and_neighbors[: data.num_nodes]

                    nodes_and_neighbors = nodes_and_neighbors[mask]
                    # print("baba2")

                    pred_out = preds.max(1)[1].to(device)
                    pred_out_ps = torch.exp(preds)
                    #
                    #
                    # Increment each node in dict by (num_test_Target) e.g 630 as well as the values for ease of "continuing" the graph since each graph is recreated
                    # # This will allow shuffling of posteriors in the attack model not to loose the node info
                    # print("newwwwwwww test", nodes_and_neighbors)

                    incremented_nodes_and_neighbors = []  # {}
                    # # for i in range(len(nodes_and_neighbors)):
                    # #     # print(nodes_and_neighbors[i])  # list
                    # #     res = [x + num_test_Target for x in nodes_and_neighbors[i]]
                    # #     incremented_nodes_and_neighbors[i+num_test_Target] = res
                    #
                    for i in range(len(nodes_and_neighbors)):
                        # print(nodes_and_neighbors[i])  # list
                        # print(nodes_and_neighbors[i][0])
                        # print(nodes_and_neighbors[i][1])

                        res = [
                            x + num_test_Target for x in nodes_and_neighbors[i][1]
                        ]  # increment from 630 num_test_Target
                        res_0 = nodes_and_neighbors[i][0] + data.num_nodes
                        incremented_nodes_and_neighbors.append((res_0, res))

                    # print("incremented_nodes_and_neighbors", incremented_nodes_and_neighbors)

                    np.save(
                        save_target_OutTrain_nodes_neigbors,
                        incremented_nodes_and_neighbors,
                    )

                    # Need to save the node info along side for this one cos this is no more sequential cos of the masking. To be used in the target_data_for_testing_outTrain in attack
                    # Simply the nodes are the last column of the "posterior"
                    nodes = []
                    for i in range(0, len(incremented_nodes_and_neighbors)):
                        nodes.append(incremented_nodes_and_neighbors[i][0])
                    nodes = np.array(nodes)
                    # print("nodesnodes",nodes)
                    preds_and_nodes = np.column_stack(
                        (pred_out_ps.cpu().detach().numpy(), nodes)
                    )
                    # print("preds_and_nodes test", preds_and_nodes.shape)
                    np.savetxt(
                        save_target_OutTrain, preds_and_nodes
                    )  # pred_out_ps.cpu().detach().numpy()

                    # print("End OutTrain for target")
                    #
                    #
                    #
                    pred_labels = pred_out.tolist()
                    true_labels = data_new.all_y[data_new.target_test_mask].tolist()

                    # The train accuracy is not on the full graph. It's similar to approx_train_acc
                    train_acc = get_train_acc(data_new, pred_Intrain)
                    # Test n val are on full graph
                    test_acc = get_test_acc(data_new, pred_out)

                else:
                    """InTrain Shadow"""
                    # pred_Intrain = model(data_new.shadow_x, data_new.shadow_edge_index)[data_new.shadow_train_mask].max(1)[1]
                    pred = []
                    nodes_and_neighbors = []
                    for batch_size, n_id, adjs in shadow_train_loader:
                        # `adjs` holds a list of `(edge_index, e_id, size)` tuples.
                        adjs = [adj.to(device) for adj in adjs]
                        # print("adjs test", adjs)
                        # print("n_id", len(n_id))

                        out, node_and_neigh = model(data_new.shadow_x[n_id], adjs)
                        out = torch.exp(out)
                        # print("out test", out.shape)
                        pred.append(out.cpu())
                        nodes_and_neighbors.append(node_and_neigh)

                    # Need to concat all preds cos it's per batch
                    pred_all_inTrain = torch.cat(pred, dim=0)

                    # pred, nodes_and_neighbors = model(data_new.shadow_x,data_new.shadow_edge_index)
                    pred_Intrain = pred_all_inTrain.max(1)[1].to(device)
                    # # Actual probabilities
                    # # pred_Intrain_ps = torch.exp(model(data_new.shadow_x,data_new.shadow_edge_index)[data_new.shadow_train_mask])
                    pred_Intrain_ps = pred_all_inTrain  # torch.exp(pred)
                    # print("pred_Intrain_ps.cpu().detach().numpy()", pred_Intrain_ps.cpu().detach().numpy())
                    np.savetxt(
                        save_shadow_InTrain, pred_Intrain_ps.cpu().detach().numpy()
                    )
                    #
                    # np.save(save_shadow_InTrain_nodes_neigbors, nodes_and_neighbors)  # No need to save cos its shadow. We dont need neighbor info
                    # print("nodes_and_neighborsnodes_and_neighbors", nodes_and_neighbors) # 630

                    # print("End InTrain for shadow")

                    """OutTrain Shadow"""
                    out, nodes_and_neighbors = model.inference(data_new.all_x)
                    # print("out OutTrain Shadow", out.shape)

                    y_true = data_new.all_y.cpu().unsqueeze(-1)
                    y_pred = out.argmax(dim=-1, keepdim=True)

                    # print(y_pred[data_new.shadow_train_mask])

                    # results = []
                    # for mask in [data_new.shadow_train_mask, data_new.shadow_test_mask]:
                    #     results += [int(y_pred[mask].eq(y_true[mask]).sum()) / int(mask.sum())]

                    # train_acc = int(y_pred[data_new.shadow_train_mask].eq(y_true[data_new.shadow_train_mask]).sum()) / int(
                    #     data_new.shadow_train_mask.sum())
                    # test_acc = int(y_pred[data_new.shadow_test_mask].eq(y_true[data_new.shadow_test_mask]).sum()) / int(
                    #     data_new.shadow_test_mask.sum())

                    # # preds, nodes_and_neighbors = model(data_new.all_x, data_new.all_edge_index)[data_new.shadow_test_mask]
                    # preds, nodes_and_neighbors = model(data_new.all_x, data_new.all_edge_index)#[data_new.shadow_test_mask]
                    nodes_and_neighbors = np.array(nodes_and_neighbors)
                    # print("type(preds)", type(preds), "type(nodes_and_neighbors)", type(nodes_and_neighbors))
                    # print("preds.shape", preds.shape)
                    # print("nodes_and_neighbors.shape", nodes_and_neighbors.shape)  # 2708
                    #
                    preds = out[data_new.shadow_test_mask]
                    # print("predsssssssssssssssss", torch.exp(preds).shape)
                    mask = data_new.shadow_test_mask.gt(
                        0
                    )  # trick to convert to true false for masking nodes_and_neighbors cos its a numpy array
                    mask = mask.cpu().numpy()
                    # print("data_new.shadow_test_mask", data_new.shadow_test_mask)
                    # print("mask", mask)
                    # print("nodes_and_neighborsnodes_and_neighbors", nodes_and_neighbors)

                    nodes_and_neighbors = nodes_and_neighbors[: data.num_nodes]

                    nodes_and_neighbors = nodes_and_neighbors[mask]
                    # print("baba2")

                    pred_out = preds.max(1)[1].to(device)
                    pred_out_ps = torch.exp(preds)
                    #
                    #
                    incremented_nodes_and_neighbors = []  # {}
                    # # for i in range(len(nodes_and_neighbors)):
                    # #     # print(nodes_and_neighbors[i])  # list
                    # #     res = [x + num_test_Shadow for x in nodes_and_neighbors[i]]
                    # #     incremented_nodes_and_neighbors[i+num_test_Shadow] = res
                    #
                    for i in range(len(nodes_and_neighbors)):
                        # print(nodes_and_neighbors[i])  # list
                        # print(nodes_and_neighbors[i][0])
                        # print(nodes_and_neighbors[i][1])

                        res = [
                            x + num_test_Shadow for x in nodes_and_neighbors[i][1]
                        ]  # increment from 630 num_test_Shadow
                        res_0 = nodes_and_neighbors[i][0] + data.num_nodes
                        incremented_nodes_and_neighbors.append((res_0, res))

                    # print("incremented_nodes_and_neighbors", incremented_nodes_and_neighbors)

                    # np.save(save_shadow_OutTrain_nodes_neigbors, incremented_nodes_and_neighbors)

                    # Need to save the node info along side for this one cos this is no more sequential cos of the masking. To be used in the shadow_data_for_testing_outTrain in attack
                    # Simply the nodes are the last column of the "posterior"
                    nodes = []
                    for i in range(0, len(incremented_nodes_and_neighbors)):
                        nodes.append(incremented_nodes_and_neighbors[i][0])
                    nodes = np.array(nodes)
                    # print("nodesnodes", nodes)
                    preds_and_nodes = np.column_stack(
                        (pred_out_ps.cpu().detach().numpy(), nodes)
                    )
                    # print("preds_and_nodes test", preds_and_nodes.shape)
                    np.savetxt(
                        save_shadow_OutTrain, pred_out_ps.cpu().detach().numpy()
                    )  # pred_out_ps.cpu().detach().numpy(). No need for preds_and_nodes here. It;s not needed. Only applicable in inTrain

                    # print("End OutTrain for shadow")
                    #
                    #
                    #
                    pred_labels = pred_out.tolist()
                    true_labels = data_new.all_y[data_new.shadow_test_mask].tolist()
                    train_acc = get_train_acc(data_new, pred_Intrain, False)
                    # Test n val are on full graph
                    test_acc = get_test_acc(data_new, pred_out, False)

                # # Actual probabilities
                # pred_Intrain_ps = torch.exp(model(data_new.all_x,data_new.all_edge_index)[data_new.target_train_mask])

                # print("posteriors", pred_Intrain)

                # The f1 measures are on test dataset
                f1_marco = get_marco_f1(data_new, pred_labels, true_labels, label_list)
                f1_micro = get_micro_f1(data_new, pred_labels, true_labels, label_list)

                # print("****************** SAGE test End *************************")
                return train_acc, test_acc, f1_marco, f1_micro

            # -----*-----*-----*-----*-----*-----*-----*-----*-----*-----*-----*-----*-----*-----*-----*-----*
            # -----*-----*-----*-----*-----*-----*-----*-----*-----*-----*-----*-----*-----*-----*-----*-----*
            # --------------------------TRAIN PROCESS-----------------------------------------------
            best_val_acc = best_val_acc = 0

            """
            Training and testing target and shadow models
            """

            if model_type == "SAGE":
                if data_type == "CiteSeer" or data_type == "Cora":
                    model_training_epoch = 16  # 301 #16 for CiteSeer n Cora, 101 for PubMed, 301 for Flickr n Reddit
                elif data_type == "PubMed":
                    model_training_epoch = 101
                else:
                    model_training_epoch = 301
            else:
                model_training_epoch = 301  # 301
            model_training_epoch_old_target = 2

            # Target train
            # for epoch in range(1, model_training_epoch_old_target):
            #     if model_type == "SAGE":
            #         approx_train_acc, train_loss = train_SAGE(
            #             target_model, target_optimizer
            #         )
            #         train_acc, test_acc, marco, micro = test_SAGE(target_model)
            #     else:
            #         approx_train_acc, train_loss = train(target_model, target_optimizer)
            #         train_acc, test_acc, marco, micro = test(target_model)
            #     # print("approx train acc", approx_train_acc, "train_loss", train_loss)

            #     # train_acc, test_acc,marco,micro = test(target_model)
            #     # if val_acc > best_val_acc:
            #     #     best_val_acc = val_acc
            #     #     test_acc = tmp_test_acc
            #     #     marco = tmp_marco
            #     #     micro = tmp_micro

            #     # log = 'Epoch: {:03d}, Train: {:.4f}, Val: {:.4f}, Test: {:.4f},marco: {:.4f},micro: {:.4f}'
            #     # print(log.format(epoch, train_acc, best_val_acc, test_acc,marco,micro))
            #     log = "TargetModel Epoch: {:03d}, Approx Train: {:.4f}, Train: {:.4f}, Test: {:.4f},marco: {:.4f},micro: {:.4f}"
            #     print(
            #         log.format(
            #             epoch, approx_train_acc, train_acc, test_acc, marco, micro
            #         )
            #     )
            #     if epoch == model_training_epoch - 1:
            #         result_file.write(
            #             log.format(
            #                 epoch, approx_train_acc, train_acc, test_acc, marco, micro
            #             )
            #             + "\n"
            #         )

            # print()
            # print(
            #     "=========================================================End Target Train =============================="
            # )

            # Shadow train
            print("shadow training")
            for epoch in tqdm(range(1, model_training_epoch)):
                if model_type == "SAGE":
                    approx_train_acc, train_loss = train_SAGE(
                        shadow_model, shadow_optimizer, False
                    )
                    train_acc, test_acc, marco, micro = test_SAGE(shadow_model, False)
                else:
                    approx_train_acc, train_loss = train(
                        shadow_model, shadow_optimizer, False
                    )
                    train_acc, test_acc, marco, micro = test(shadow_model, False)
                # print("approx train acc", approx_train_acc, "train_loss", train_loss)

                # train_acc, test_acc,marco,micro = test(shadow_model)
                # if val_acc > best_val_acc:
                #     best_val_acc = val_acc
                #     test_acc = tmp_test_acc
                #     marco = tmp_marco
                #     micro = tmp_micro

                # log = 'Epoch: {:03d}, Train: {:.4f}, Val: {:.4f}, Test: {:.4f},marco: {:.4f},micro: {:.4f}'
                # print(log.format(epoch, train_acc, best_val_acc, test_acc,marco,micro))
                log = "ShadowModel Epoch: {:03d}, Approx Train: {:.4f}, Train: {:.4f}, Test: {:.4f},marco: {:.4f},micro: {:.4f}"
                # print(
                #     log.format(
                #         epoch, approx_train_acc, train_acc, test_acc, marco, micro
                #     )
                # )
                if epoch == model_training_epoch - 1:
                    result_file.write(
                        log.format(
                            epoch, approx_train_acc, train_acc, test_acc, marco, micro
                        )
                        + "\n"
                    )
            print("shadow training done")

            """ =========================================== ATTACK ============================================== """

            # Use normal python to import posterior files.
            # Split posterior data into 80 / 20 (train, test)

            # add 2 dataset 2 gether pandas
            # Add 0 to 629 (num_test_Target) to train posterior {target_data_for_testing_Intrain} and 630 to 1259 (num_test_Target x 2) to test posterior in attack data

            positive_attack_data = pd.read_csv(
                save_shadow_InTrain, header=None, sep=" "
            )  # dataframe #"posteriorsShadowTrain.txt"
            # target in and out data

            # Assign 1 to indata
            # transfer array to dataframe
            if args["dataset_name"] == "cora":
                target_data_for_testing_Intrain = pd.DataFrame(
                    self.train_posterior.cpu().detach().numpy(),
                    columns=[
                        "0",
                        "1",
                        "2",
                        "3",
                        "4",
                        "5",
                        "6",
                    ],
                )
            elif args["dataset_name"] == "CS" or args["dataset_name"] == "Coauthor_CS":
                target_data_for_testing_Intrain = pd.DataFrame(
                    self.train_posterior.cpu().detach().numpy(),
                    columns=[
                        "0",
                        "1",
                        "2",
                        "3",
                        "4",
                        "5",
                        "6",
                        "7",
                        "8",
                        "9",
                        "10",
                        "11",
                        "12",
                        "13",
                        "14",
                    ],
                )

            # target_data_for_testing_Intrain = pd.read_csv(
            #     save_target_InTrain, header=None, sep=" "
            # )  # dataframe "posteriorsTargetTrain.txt"

            target_data_for_testing_Intrain["labels"] = 1

            target_data_for_testing_Intrain["nodeID"] = range(
                0, self.train_posterior.shape[0]
            )  # num_test_Target 630 first save

            # target_data_for_testing_Intrain["nodeID"] = (
            #     target_data_for_testing_Intrain.iloc[:, -1:].astype(float).astype(int)
            # )  # selects last column #range(0, num_test_Target) #num_test_Target, num_test_Target+num_test_Target
            # print("target_data_for_testing_Intrain.head(10)", target_data_for_testing_Intrain.head(10))
            # print("target_data_for_testing_Intrain.tail(10)", target_data_for_testing_Intrain.tail(10))

            # # randomly select 500
            # chosen_idx = np.random.choice(153431, replace=False, size=50000)
            # print(chosen_idx)
            # positive_attack_data = positive_attack_data.iloc[chosen_idx]

            # transfer to dataframe
            if args["dataset_name"] == "cora":
                target_data_for_testing_Outtrain = pd.DataFrame(
                    self.test_posterior.cpu().detach().numpy(),
                    columns=[
                        "0",
                        "1",
                        "2",
                        "3",
                        "4",
                        "5",
                        "6",
                    ],
                )
            elif args["dataset_name"] == "CS" or args["dataset_name"] == "Coauthor_CS":
                target_data_for_testing_Outtrain = pd.DataFrame(
                    self.test_posterior.cpu().detach().numpy(),
                    columns=[
                        "0",
                        "1",
                        "2",
                        "3",
                        "4",
                        "5",
                        "6",
                        "7",
                        "8",
                        "9",
                        "10",
                        "11",
                        "12",
                        "13",
                        "14",
                    ],
                )

            # target_data_for_testing_Outtrain_data = pd.read_csv(
            #     save_target_OutTrain, header=None, sep=" "
            # )  # dataframe "posteriorsTargetOut.txt"

            # target_data_for_testing_Outtrain = (
            #     target_data_for_testing_Outtrain_data.iloc[:, :-1]
            # )  # drop last. To be assigned later as nodeID

            target_data_for_testing_Outtrain["nodeID"] = range(
                0, self.test_posterior.shape[0]
            )
            # target_data_for_testing_Outtrain["nodeID"] = (
            #     target_data_for_testing_Outtrain_data.iloc[:, -1:]
            #     .astype(float)
            #     .astype(int)
            # )  # selects last column #range(num_test_Target, data.num_nodes+data.num_nodes) #num_test_Target, num_test_Target+num_test_Target
            # print("target_data_for_testing_Outtrain", target_data_for_testing_Outtrain)
            # print(positive_attack_data.head())

            # Assign 0 to outdata
            target_data_for_testing_Outtrain["labels"] = 0

            # Assign 1 to training data
            positive_attack_data["labels"] = 1

            # print("positive_attack_data.shape", positive_attack_data.shape)

            negative_attack_data = pd.read_csv(
                save_shadow_OutTrain, header=None, sep=" "
            )  # "posteriorsShadowOut.txt"

            # # randomly select 140
            # chosen_idx = np.random.choice(55703, replace=False, size=50000)
            # print(chosen_idx)
            # negative_attack_data = negative_attack_data.iloc[chosen_idx]

            # print(negative_attack_data.head())

            # Assign 0 to out data
            negative_attack_data["labels"] = 0
            # print("negative_attack_data.shape", negative_attack_data.shape)

            # Combine to single dataframe

            # combine them together
            attack_data_combo = [positive_attack_data, negative_attack_data]
            attack_data = pd.concat(attack_data_combo)

            target_data_for_testing_InAndOutTrain_combo = [
                target_data_for_testing_Intrain,
                target_data_for_testing_Outtrain,
            ]
            target_data_for_testing_InAndOutTrain = pd.concat(
                target_data_for_testing_InAndOutTrain_combo, sort=False
            )

            # print(
            #     "target_data_for_testing_InAndOutTrain",
            #     target_data_for_testing_InAndOutTrain.shape,
            # )

            # print("attack_data.shape", attack_data.shape)
            # print(attack_data.head())

            # # sample randomly
            # # returns all but in a random fashion
            # attack_data = attack_data.sample(frac=1)
            # print(attack_data.head())

            X_attack = attack_data.drop("labels", axis=1)
            # print("X_attack.shape", X_attack.shape)

            y_attack = attack_data["labels"]

            # let's do in and out for attack data (shadow)
            X_attack_InTrain = positive_attack_data.drop("labels", axis=1)
            y_attack_InTrain = positive_attack_data["labels"]

            X_attack_OutTrain = negative_attack_data.drop("labels", axis=1)
            y_attack_OutTrain = negative_attack_data["labels"]

            # print("X_attack_InTrain", X_attack_InTrain.shape)
            # print("X_attack_OutTrain", X_attack_OutTrain.shape)

            # For in train data (target)
            X_InTrain = target_data_for_testing_Intrain.drop(
                ["labels", "nodeID"], axis=1
            )
            y_InTrain = target_data_for_testing_Intrain["labels"]
            nodeID_InTrain = target_data_for_testing_Intrain["nodeID"]

            # For Out train data
            X_OutTrain = target_data_for_testing_Outtrain.drop(
                ["labels", "nodeID"], axis=1
            )
            y_OutTrain = target_data_for_testing_Outtrain["labels"]
            nodeID_OutTrain = target_data_for_testing_Outtrain["nodeID"]

            # For in out data
            X_InOutTrain = target_data_for_testing_InAndOutTrain.drop(
                ["labels", "nodeID"], axis=1
            )
            # print("X_InTrain.shape", X_InOutTrain.shape)

            y_InOutTrain = target_data_for_testing_InAndOutTrain["labels"]
            nodeID_InOutTrain = target_data_for_testing_InAndOutTrain["nodeID"]

            # convert to numpy
            # for shadow
            X_attack_InOut, y_attack_InOut = X_attack.to_numpy(), y_attack.to_numpy()

            X_attack_InTrain, X_attack_OutTrain = (
                X_attack_InTrain.to_numpy(),
                X_attack_OutTrain.to_numpy(),
            )
            y_attack_InTrain, y_attack_OutTrain = (
                y_attack_InTrain.to_numpy(),
                y_attack_OutTrain.to_numpy(),
            )

            # for target
            X_InTrain, y_InTrain, nodeID_InTrain = (
                X_InTrain.to_numpy(),
                y_InTrain.to_numpy(),
                nodeID_InTrain.to_numpy(),
            )
            X_OutTrain, y_OutTrain, nodeID_OutTrain = (
                X_OutTrain.to_numpy(),
                y_OutTrain.to_numpy(),
                nodeID_OutTrain.to_numpy(),
            )

            # for target
            X_InOutTrain, y_InOutTrain, nodeID_InOutTrain = (
                X_InOutTrain.to_numpy(),
                y_InOutTrain.to_numpy(),
                nodeID_InOutTrain.to_numpy(),
            )

            # # Plot graphs
            #
            # plt.imshow(X_attack_InTrain, interpolation='nearest', aspect='auto')
            # plt.colorbar()
            # plt.tight_layout()
            # plt.title('Positive: In Train Posteriors')
            # plt.show()
            #
            # plt.imshow(X_attack_OutTrain, interpolation='nearest', aspect='auto')
            # plt.colorbar()
            # plt.tight_layout()
            # plt.title('Negative: Out Train Posteriors')
            # plt.show()
            #
            #
            # plt.imshow(X_InTrain, interpolation='nearest', aspect='auto')
            # plt.colorbar()
            # plt.tight_layout()
            # plt.title('Positive: Target Posteriors')
            # plt.show()
            #
            # plt.imshow(X_OutTrain, interpolation='nearest', aspect='auto')
            # plt.colorbar()
            # plt.tight_layout()
            # plt.title('Negative: Target Posteriors')
            # plt.show()

            (
                attack_train_data_X,
                attack_test_data_X,
                attack_train_data_y,
                attack_test_data_y,
            ) = train_test_split(
                X_attack,
                y_attack,
                test_size=50,
                stratify=y_attack,
                random_state=rand_state,
            )  # this train_test split is for attack, before train_test split for shadow model training

            # convert series data to numpy array
            (
                attack_train_data_X,
                attack_test_data_X,
                attack_train_data_y,
                attack_test_data_y,
            ) = (
                attack_train_data_X.to_numpy(),
                attack_test_data_X.to_numpy(),
                attack_train_data_y.to_numpy(),
                attack_test_data_y.to_numpy(),
            )

            # print("Attack data printing...")
            # print(attack_test_data_X, attack_test_data_y)

            # Attack_train
            attack_train_data = torch.utils.data.TensorDataset(
                torch.from_numpy(attack_train_data_X).float(),
                torch.from_numpy(attack_train_data_y),
            )  # convert to float to fix  uint8_t overflow error
            attack_train_data_loader = torch.utils.data.DataLoader(
                attack_train_data, batch_size=32, shuffle=True
            )

            # Attack_test = combo of targettrain and targetOut
            attack_test_data = torch.utils.data.TensorDataset(
                torch.from_numpy(attack_test_data_X).float(),
                torch.from_numpy(attack_test_data_y),
            )  # convert to float to fix  uint8_t overflow error
            attack_test_data_loader = torch.utils.data.DataLoader(
                attack_test_data, batch_size=32, shuffle=True
            )

            # Training InData
            target_data_for_testing_InTrain_data = torch.utils.data.TensorDataset(
                torch.from_numpy(X_InTrain).float(),
                torch.from_numpy(y_InTrain),
                torch.from_numpy(nodeID_InTrain),
            )
            target_data_for_testing_InTrain_data_loader = torch.utils.data.DataLoader(
                target_data_for_testing_InTrain_data, batch_size=64, shuffle=False
            )

            # Training OutData
            target_data_for_testing_OutTrain_data = torch.utils.data.TensorDataset(
                torch.from_numpy(X_OutTrain).float(),
                torch.from_numpy(y_OutTrain),
                torch.from_numpy(nodeID_OutTrain),
            )

            target_data_for_testing_OutTrain_data_loader = torch.utils.data.DataLoader(
                target_data_for_testing_OutTrain_data, batch_size=64, shuffle=False
            )

            # Training InOut Data
            target_data_for_testing_InOutTrain_data = torch.utils.data.TensorDataset(
                torch.from_numpy(X_InOutTrain).float(),
                torch.from_numpy(y_InOutTrain),
                torch.from_numpy(nodeID_InOutTrain),
            )
            target_data_for_testing_InOutTrain_data_loader = (
                torch.utils.data.DataLoader(
                    target_data_for_testing_InOutTrain_data, batch_size=64, shuffle=True
                )
            )

            # features, labels = next(iter(attack_test_data_loader))
            # print(features, labels)

            class AttackModel(nn.Module):
                def __init__(self):
                    super().__init__()

                    # inputs to hidden layer linear transformation
                    # Note, when using Linear, weight and biases are randomly initialized for you
                    self.hidden = nn.Linear(dataset.num_classes, 100)
                    self.hidden2 = nn.Linear(100, 50)
                    # output layer, 10 units - one for each digits
                    self.output = nn.Linear(50, 2)

                    # # Define sigmoid activation and softmax output
                    # # comment this cos u can just define directly if u are using functional
                    # self.sigmoid = nn.Sigmoid()
                    # self.softmax = nn.Softmax(dim=1)

                def forward(self, x):
                    # # pass the input tensor through each of our operations
                    # # comment to use functional
                    # x = self.hidden(x)
                    # x = self.sigmoid(x)
                    # x = self.output(x)
                    # x = self.softmax(x)

                    # Hidden layer with sigmoid activation
                    x = F.sigmoid(self.hidden(x))
                    x = F.sigmoid(self.hidden2(x))
                    # output layer with softmax activation
                    x = F.softmax(self.output(x), dim=1)
                    # print("xxxxxxxx", x)

                    return x

            class Net(nn.Module):
                # define nn
                def __init__(self):
                    super(Net, self).__init__()
                    self.fc1 = nn.Linear(dataset.num_classes, 100)
                    self.fc2 = nn.Linear(100, 50)
                    self.fc3 = nn.Linear(50, 2)
                    self.softmax = nn.Softmax(dim=1)
                    self.dropout = nn.Dropout(p=0.5)

                def forward(self, X):
                    # print("attack X",X)
                    X = F.relu(self.fc1(X))
                    X = self.dropout(X)
                    X = F.relu(self.fc2(X))
                    X = self.fc3(X)
                    X = self.softmax(X)

                    return X

            def init_weights(m):
                if type(m) == nn.Linear:
                    torch.nn.init.xavier_uniform(m.weight)
                    m.bias.data.fill_(0.01)

            # create the ntwk
            attack_model = Net()  # AttackModel()
            attack_model = attack_model.to(device)
            attack_model.apply(init_weights)  # initialize weight rather than randomly
            # print(attack_model)

            def attack_train(
                model, trainloader, testloader, criterion, optimizer, epochs, steps=0
            ):
                # train ntwk

                # Decay LR by a factor of 0.1 every 7 epochs
                # scheduler = lr_scheduler.StepLR(optimizer, step_size=7, gamma=0.1)
                print("attack training")
                final_train_loss = 0
                train_losses, test_losses = [], []
                posteriors = []
                for e in tqdm(range(epochs)):
                    running_loss = 0
                    train_accuracy = 0

                    # This is features, labels cos we dont care about nodeID during training! only during test
                    for features, labels in trainloader:
                        model.train()
                        features, labels = features.to(device), labels.to(device)

                        # print("post shape", features.shape)
                        # print("labels",labels)
                        optimizer.zero_grad()
                        # print("features", features.shape)

                        # features = features.unsqueeze(1) #unsqueeze
                        # flatten features
                        features = features.view(features.shape[0], -1)

                        logps = model(features)  # log probabilities
                        # print("labelsssss", labels.shape)
                        loss = criterion(logps, labels)

                        # Actual probabilities
                        ps = logps  # torch.exp(logps) #Only use this if the loss is nlloss
                        # print("ppppp",ps)

                        top_p, top_class = ps.topk(
                            1, dim=1
                        )  # top_p gives the probabilities while top_class gives the predicted classes
                        # print(top_p)
                        equals = top_class == labels.view(
                            *top_class.shape
                        )  # making the shape of the label and top class the same
                        train_accuracy += torch.mean(equals.type(torch.FloatTensor))

                        loss.backward()
                        optimizer.step()

                        running_loss += loss.item()
                    else:
                        # Everything in this else block executes after every epock
                        # print(f"training loss: {running_loss}")

                        # test_loss = 0
                        # test_accuracy = 0
                        #
                        # # Turn off gradients for validation, saves memory and computations
                        # with torch.no_grad():
                        #     # Doing validation
                        #
                        #     # set model to evaluation mode
                        #     model.eval()
                        #
                        #     if e == epochs - 1:
                        #         print("Doing attack validation===========")
                        #     # validation pass
                        #
                        #     for features, labels in testloader:
                        #         # features = features.unsqueeze(1)  # unsqueeze
                        #         features = features.view(features.shape[0], -1)
                        #         logps = model(features)
                        #         test_loss += criterion(logps, labels)
                        #
                        #         # Actual probabilities
                        #         ps = torch.exp(logps)
                        #
                        #         top_p, top_class = ps.topk(1,
                        #                                    dim=1)  # top_p gives the probabilities while top_class gives the predicted classes
                        #         # print(top_p)
                        #         equals = top_class == labels.view(
                        #             *top_class.shape)  # making the shape of the label and top class the same
                        #         test_accuracy += torch.mean(equals.type(torch.FloatTensor))
                        test_loss, test_accuracy, _, _, _, _, _, _, _ = attack_test(
                            model, testloader, trainTest=True
                        )

                        # set model back yo train model
                        model.train()
                        # scheduler.step()

                        train_losses.append(running_loss / len(trainloader))
                        test_losses.append(test_loss)

                        # get final train loss. To be returned at the end of the training loop
                        final_train_loss = running_loss / len(trainloader)

                        # print(
                        #     "Epoch: {}/{}..".format(e + 1, epochs),
                        #     "Training loss: {:.5f}..".format(
                        #         running_loss / len(trainloader)
                        #     ),
                        #     "Test Loss: {:.5f}..".format(test_loss),
                        #     "Train Accuracy: {:.3f}".format(
                        #         train_accuracy / len(trainloader)
                        #     ),
                        #     "Test Accuracy: {:.3f}".format(test_accuracy),
                        # )

                # # plot train and test loss
                # plt.show()
                # plt.plot(train_losses)
                # plt.plot(test_losses)
                # plt.title('Model Losses')
                # plt.ylabel('loss')
                # plt.xlabel('epoch')
                # plt.legend(['train', 'val'], loc='upper left')
                # plt.show()
                print("attack training done")
                return final_train_loss

            def attack_test(model, testloader, singleClass=False, trainTest=False):
                test_loss = 0
                test_accuracy = 0
                auroc = 0
                precision = 0
                recall = 0
                f_score = 0

                posteriors = []
                all_nodeIDs = []
                true_predicted_nodeIDs_and_class = {}
                false_predicted_nodeIDs_and_class = {}

                # Turn off gradients for validation, saves memory and computations
                with torch.no_grad():
                    # Doing validation

                    # set model to evaluation mode
                    model.eval()

                    if trainTest:
                        for features, labels in testloader:
                            features, labels = features.to(device), labels.to(device)
                            # features = features.unsqueeze(1)  # unsqueeze
                            features = features.view(features.shape[0], -1)
                            logps = model(features)
                            test_loss += criterion(logps, labels)

                            # Actual probabilities
                            ps = logps  # torch.exp(logps)
                            posteriors.append(ps)

                            # if singleclass=false
                            if not singleClass:
                                y_true = labels.cpu().unsqueeze(-1)
                                # print("y_true", y_true)
                                y_pred = ps.argmax(dim=-1, keepdim=True)
                                # print("y_pred", y_pred)

                                # uncomment this to show AUROC
                                auroc += roc_auc_score(
                                    y_true.cpu().numpy(), y_pred.cpu().numpy()
                                )
                                # print("auroc", auroc)

                                precision += precision_score(
                                    y_true.cpu().numpy(),
                                    y_pred.cpu().numpy(),
                                    average="weighted",
                                )

                                recall += recall_score(
                                    y_true.cpu().numpy(),
                                    y_pred.cpu().numpy(),
                                    average="weighted",
                                )

                                f_score += f1_score(
                                    y_true.cpu().numpy(),
                                    y_pred.cpu().numpy(),
                                    average="weighted",
                                )

                            top_p, top_class = ps.topk(
                                1, dim=1
                            )  # top_p gives the probabilities while top_class gives the predicted classes
                            # print(top_p)
                            equals = top_class == labels.view(
                                *top_class.shape
                            )  # making the shape of the label and top class the same
                            test_accuracy += torch.mean(equals.type(torch.FloatTensor))

                    else:
                        # print("len(testloader.dataset)", len(testloader.dataset))
                        for features, labels, nodeIDs in testloader:
                            # print("nodeIDs", nodeIDs)
                            features, labels = features.to(device), labels.to(device)
                            # features = features.unsqueeze(1)  # unsqueeze
                            features = features.view(features.shape[0], -1)
                            logps = model(features)
                            test_loss += criterion(logps, labels)

                            # Actual probabilities
                            ps = logps  # torch.exp(logps)
                            posteriors.append(ps)

                            # print("ps", ps)
                            # print("nodeIDs", nodeIDs)

                            all_nodeIDs.append(nodeIDs)

                            # if singleclass=false
                            if not singleClass:
                                y_true = labels.cpu().unsqueeze(-1)
                                # print("y_true", y_true)
                                y_pred = ps.argmax(dim=-1, keepdim=True)
                                # print("y_pred", y_pred)

                                # uncomment this to show AUROC
                                auroc += roc_auc_score(
                                    y_true.cpu().numpy(), y_pred.cpu().numpy()
                                )
                                # print("auroc", auroc)

                                precision += precision_score(
                                    y_true.cpu().numpy(),
                                    y_pred.cpu().numpy(),
                                    average="weighted",
                                )

                                recall += recall_score(
                                    y_true.cpu().numpy(),
                                    y_pred.cpu().numpy(),
                                    average="weighted",
                                )

                                f_score += f1_score(
                                    y_true.cpu().numpy(),
                                    y_pred.cpu().numpy(),
                                    average="weighted",
                                )

                            top_p, top_class = ps.topk(
                                1, dim=1
                            )  # top_p gives the probabilities while top_class gives the predicted classes
                            # print("top_p", top_p)
                            # print("top_class", top_class)

                            equals = top_class == labels.view(
                                *top_class.shape
                            )  # making the shape of the label and top class the same

                            # print("equals", len(equals))
                            for i in range(len(equals)):
                                if equals[
                                    i
                                ]:  # if element is true {meaning both member n non-member}, get the nodeID
                                    # print("baba")
                                    # print("true pred nodeIDs", nodeIDs[i])
                                    true_predicted_nodeIDs_and_class[
                                        nodeIDs[i].item()
                                    ] = top_class[i].item()
                                    # print("len(true_predicted_nodeIDs_and_class)", len(true_predicted_nodeIDs_and_class),"nodeID--",nodeIDs[i].item(), "class--",  top_class[i].item())
                                else:
                                    false_predicted_nodeIDs_and_class[
                                        nodeIDs[i].item()
                                    ] = top_class[i].item()
                                    # print("len(false_predicted_nodeIDs_and_class)", len(false_predicted_nodeIDs_and_class))

                            test_accuracy += torch.mean(equals.type(torch.FloatTensor))

                test_accuracy = test_accuracy / len(testloader)
                test_loss = test_loss / len(testloader)
                final_auroc = auroc / len(testloader)
                final_precision = precision / len(testloader)
                final_recall = recall / len(testloader)
                final_f_score = f_score / len(testloader)

                # print('final precision', final_precision)
                # print('final micro precision', final_recall)

                # print("final auroc", final_auroc)
                # if all_nodeIDs:
                #     print("all_nodeIDs", torch.cat(all_nodeIDs, 0), "shape Cat", torch.cat(all_nodeIDs, 0).shape)
                #     # true_predicted_nodeIDs_and_class = torch.cat(true_predicted_nodeIDs_and_class)

                return (
                    test_loss,
                    test_accuracy,
                    posteriors,
                    final_auroc,
                    final_precision,
                    final_recall,
                    final_f_score,
                    true_predicted_nodeIDs_and_class,
                    false_predicted_nodeIDs_and_class,
                )

            """Initialization / params for attack model"""

            criterion = nn.CrossEntropyLoss()  # nn.NLLLoss() # cross entropy loss

            optimizer = torch.optim.Adam(
                attack_model.parameters(), lr=0.01
            )  # 0.01 #0.00001

            epochs = 300  # 1000

            """==============Train and test Attack model ========== """

            attack_train(
                attack_model,
                attack_train_data_loader,
                attack_test_data_loader,
                criterion,
                optimizer,
                epochs,
            )

            # test to confirm using attack_test_data_loader
            (
                _,
                test_accuracyConfirmTest,
                posteriors,
                auroc,
                precision,
                recall,
                f_score,
                _,
                _,
            ) = attack_test(attack_model, attack_test_data_loader, trainTest=True)
            # print(posteriors)

            # This is d result on the test set we used i.e split the attack data into train and test.
            # Size of the test = 50
            # print(
            #     "To confirm using attack_test_data_loader (50 test samples): {:.3f}".format(
            #         test_accuracyConfirmTest
            #     ),
            #     "AUROC: {:.3f}".format(auroc),
            #     "precision: {:.3f}".format(precision),
            #     "recall {:.3f}".format(recall),
            # )

            # test for InOut train target data
            # This is the one we are interested in
            (
                _,
                test_accuracyInOut,
                posteriors,
                auroc,
                precision,
                recall,
                f_score,
                true_predicted_nodeIDs_and_class,
                false_predicted_nodeIDs_and_class,
            ) = attack_test(
                attack_model, target_data_for_testing_InOutTrain_data_loader
            )
            # print(posteriors)
            # print("true_predicted_nodeIDs_and_class", len(true_predicted_nodeIDs_and_class))
            # print("false_predicted_nodeIDs_and_class", len(false_predicted_nodeIDs_and_class))
            print(
                "Test accuracy: {:.3f}".format(test_accuracyInOut),
                "AUROC: {:.3f}".format(auroc),
                "precision: {:.3f}".format(precision),
                "recall {:.3f}".format(recall),
                "F1 score {:.3f}".format(f_score),
                "===> Attack Performance!",
            )

            result_file.write(
                "Test accuracy with Target Train InOut: {:.3f} ".format(
                    test_accuracyInOut
                )
                + " AUROC: {:.3f}".format(auroc)
                + " precision: {:.3f}".format(precision)
                + " recall {:.3f}".format(recall)
                + " F1 score {:.3f}".format(f_score)
                + "===> Attack Performance! \n"
            )

            self.auc_all = auroc
            self.precision_all = precision
            # test for Only In train target data
            (
                _,
                test_accuracyIn,
                posteriors,
                _,
                precision,
                recall,
                f_score,
                _,
                _,
            ) = attack_test(
                attack_model, target_data_for_testing_InTrain_data_loader, True
            )

            self.acc_pos = test_accuracyIn
            self.f_score_pos = f_score
            # print("Test accuracy with Target Train In: {:.3f}".format(test_accuracyIn), "precision: {:.3f}".format(precision),
            #       "recall {:.3f}".format(recall), "F1 score {:.3f}".format(f_score))

            # test for Only Out train target data
            (
                _,
                test_accuracyOut,
                posteriors,
                _,
                precision,
                recall,
                f_score,
                _,
                _,
            ) = attack_test(
                attack_model, target_data_for_testing_OutTrain_data_loader, True
            )
            # print("Test accuracy with Target Train Out: {:.3f}".format(test_accuracyOut), "precision: {:.3f}".format(precision),
            #       "recall {:.3f}".format(recall), "F1 score {:.3f}".format(f_score))

            result_file.write(
                "Test accuracy with Target Train In: {:.3f} ".format(test_accuracyIn)
                + " |=====| Test accuracy with Target Train Out: {:.3f}".format(
                    test_accuracyOut
                )
                + "\n"
            )

            # print("data_type", data_type)
            # print("model_type", model_type)
            end_time = time.time()

            total_time = round(end_time - start_time, 3)
            # print("WhichRun", which_run, " Total time", total_time)

            # result_file.write("Data:"+data_type +" Model:"+ model_type+"\n\n\n")
            result_file.write(
                " ================ WhichRun: "
                + str(which_run)
                + " || Data: "
                + data_type
                + " || Model: "
                + model_type
                + " || Time: "
                + str(total_time)
                + " || rand_state: "
                + str(rand_state)
                + " ================== \n\n\n"
            )

            result_file.close()

    def get_results(self):
        return self.f_score_pos, self.acc_pos, self.auc_all, self.precision_all
