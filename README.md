# anonymous
Code for submission IDEA: A Flexible Framework of Certified Unlearning for Graph Neural Networks



## Usage of IDEA_attack
The folder `IDEA_attack` is used to attack IDEA. By using the files containing unlearned results from `./attack_materials`, run the following command to attack [node/edge/feauture].

```
cd IDEA_attack
./run_node.sh # attack node
./run_edge.sh # attack edge
./run_feature.sh # attack feature (partial or full)
```
### Note
Unlearned result filenames are supposed to follow the formats below.
```
../IDEA/attack_materials/seed_{args.run_seed_feature}_IDEA_cora_node_0.05_{args.model_name}_{args.remove_feature_ratio}.pth # attack node

../IDEA/attack_materials/seed_{args.run_seed_feature}_IDEA_cora_edge_0.05_{args.model_name}_{args.remove_feature_ratio}.pth # attack edge

../IDEA/attack_materials/seed_{args.run_seed_feature}_IDEA_cora_partial_feature_0.05_{args.model_name}_{args.remove_feature_ratio}.pth # attack feature
```


### Examples
Here we use the unlearned results of IDEA with configurations 

`dataset : Cora | unlearning_mode : node | unlearning_ratio : 0.05 | target_model : GCN`

Run

```
./run_node.sh
```
to attack the model with node unlearned. We present the sample log as follows.

```
shadow training
100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 300/300 [00:14<00:00, 20.85it/s]
shadow train done
attack training
100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 300/300 [00:22<00:00, 13.27it/s]
attack training done
Test accuracy: 0.492 AUROC: 0.513 precision: 0.492 recall 0.407 F1 score 0.407 ===> Attack Performance!
```
The result is also saved into a CSV file as `./result/node_attack_results.csv`

Dataset | Exp | Unlearn Ratio | AUC Mean | AUC Std | ACC Mean | ACC Std
:--: | :--: | :--: | :--: | :--: | :--: | :--: 
cora | node | 0.05 | 0.513 | 0.0 | 0.492 | 0.0

## Usage of GraphEraser

The folder of `Eraser` is used to reproduce the code of GraphEraser and support implementing both node attack (GraphMIA) and edge attack (StealLink). To choose different running configurations (dataset/target_model/partition_method/etc), change the parameters in run_new_[node/edge/feature].sh. Then run the following command to train & unlearn & attack.

```
cd Eraser
./run_new_node.sh # for node unlearning
./run_new_edge.sh # for edge unlearning
```
### Parameter explanation
```
--exp node # unlearning mode, within node/edge
--is_attack True # edge attack
--is_attack_node True # node attack
--is_ratio True # whether unlearn nodes by ratio/number
```

### Train & unlearn Examples

Here we consider setting as 

`dataset : cora | target_model : GCN | partition_method : random | aggregator : optimal | unlearning_mode : node`

Run
```
./run_new_node.sh
```
to train and unlearn the GCN model. With running once, we present the sample log as follows.
```
INFO:2024-02-07 13:45:19,573: - lib_graph_partition.graph_partition - : graph partition, method: random
INFO:2024-02-07 13:45:19,574: - exp_graph_partition - : generating shard data
INFO:2024-02-07 13:45:19,583: - data_store - : saving shard data
INFO:2024-02-07 13:45:19,654: - exp_node_edge_unlearning - : training target models
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 10/10 [00:04<00:00,  2.09it/s]
INFO:2024-02-07 13:45:24,430: - exp_node_edge_unlearning - : aggregating submodels
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 10/10 [00:00<00:00, 18.72it/s]
INFO:2024-02-07 13:45:25,021: - exp_node_edge_unlearning - : f1_avg: 0.6051660516605166 f1_std: 0.0 time_avg: 5.3660688400268555 time_std: 0.0
INFO:2024-02-07 13:45:25,121: - exp_attack_unlearning - : retraining the unlearned model
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 10/10 [00:02<00:00,  3.62it/s]
INFO:2024-02-07 13:45:27,883: - exp_attack_unlearning - : aggregating submodels
100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 10/10 [00:00<00:00, 21.56it/s]
INFO:2024-02-07 13:45:28,410: - exp_attack_unlearning - : f1_avg: 0.5424354243542435 f1_std: 0.0 time_avg: 3.2886276245117188 time_std: 0.0
```

The final unlearning result containing performance and unlearning time is also save into a CSV file as `temp_data/new_setting.csv`.

dataset | model | unlearn_task | is_ratio | unlearn_ratio | partition_method | aggregator | f1_score_avg | f1_score_std | training_time_avg | training_time_std | f1_score_unlearn_avg | f1_score_unlearn_std | unlearning_time_avg | unlearning_time_std 
:---: | :---: | :---: | :---: |:---: |:---: |:---: |:---: |:---: |:---: |:---: |:---: |:---: |:---: |:---:
cora | GCN | node | True | 0.05 | random | optimal | 0.4895 | 0.0191 | 12.0968 | 0.6121 | 0.4649 | 0.0197 | 11.3277 | 0.2202

### Attack Example

To attack the node unlearning, simply add the `--is_attack_node True` in the .sh script, then rerun.
```
./run_new_node.sh
```
We present part of the sample log as follows
```
INFO:2024-02-07 13:51:54,139: - exp_attack_unlearning - : attack
shadow training
100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 300/300 [00:13<00:00, 22.00it/s]
shadow training done
attack training
100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 300/300 [00:18<00:00, 15.94it/s]
attack training done
Test accuracy: 0.503 AUROC: 0.500 precision: 0.499 recall 0.503 F1 score 0.472 ===> Attack Performance!
```

The attack result is also saved into a CSV file as `result/node_attack_results.csv`

Dataset | Partition Method | Aggregator | Exp | Unlearn Ratio | AUC | AUC Std | ACC | ACC Std
:---: |:---: |:---: |:---: |:---: |:---: |:---: |:---: |:---: 
cora | random | optimal | node | 0.05 | 0.4997| 0.0 | 0.4986 | 0.0


## Usage of CGU

The folder `CGU` is used to reproduce the code of CGU and support implementing both node attack (GraphMIA) and edge attack (StealLink). To choose different running configurations (dataset/unlearning ratio/etc), change the parameters in run_new_[node/edge/feature].sh. Then run the following command to train & unlearn & attack.

```
cd CGU
./run_new_node.sh # for node unlearning
./run_new_edge.sh # for edge unlearning
./run_new_feature.sh # for feature unlearning
```

### Parameter explanation
```
--removal_mode node # unlearning mode, within node/edge
--is_attack (store_true) # edge attack
--is_attack_node (store_true) # node attack
--is_attack_feature (store_true) # feauture attack (require removed feature_dimension data from IDEA)
--is_ratio (store_true) # whether unlearn instances by ratio/number
```


### Train & unlearn Examples

Here we consider setting as 

`dataset : cora | unlearning_mode : edge`

Run
```
./run_new_edge.sh
```
to train and unlearn the GCN model. With running once, we present the sample log as follows.
```
==========Loading data==========
Dataset: cora
********** 0 **********
==========Training on full dataset with graph==========
Train node:2438, Val node:270, Test node:270, Edges:10661, Feature dim:1433
With graph, train mode: ovr , optimizer: LBFGS
==========Testing our edge removal==========
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 27/27 [00:03<00:00,  8.58it/s]
Training results: f1_avg: 0.8523, f1_std: 0.0 time_avg: 0.9792, time_std: 0.0 
Unlearning results: f1_avg: 0.8545, f1_std: 0.0 removal_time_avg: 3.1361, removal_time_std: 0.0
```

The final unlearning result containing performance and unlearning time is also save into a CSV file as `result/unlearning_results.csv`.

dataset | model | unlearn_task | is_ratio | unlearn_ratio | f1_score_avg | f1_score_std | training_time_avg | training_time_std | f1_score_unlearn_avg | f1_score_unlearn_std | unlearning_time_avg | unlearning_time_std
:---: | :---: | :---: | :---: |:---: |:---: |:---: |:---: |:---: |:---: |:---: |:---: |:---: 
cora | SGC | edge | True | 0.01 | 0.82740337 | 0.0 | 0.5913925 | 0.47879428 | 0.823591 | 0.0 | 2.897691 | 0.2393388

### Attack Example

To attack the node unlearning, simply add the `--is_attack` in the .sh script, then rerun.
```
./run_new_edge.sh
```
We present part of the sample log as follows
```
attack starts
2/2 [==============================] - 0s 882us/step
Test accuracy: 0.5 Test Precision 0.5 Test Recall 0.5185185185185185 Test auc: 0.5692729766803841
attack ends
```

The attack result for each run is also saved into a CSV file as `result/attack_results.csv`

Dataset | Exp | Unlearn Ratio | Attack Metrics | Epochs | Test Accuracy | Test Precision | Test Recall | Test AUC | Ratio
:---: |:---: |:---: |:---: |:---: |:---: |:---: |:---: |:---: | :---: 
cora | edge | 0.01 | attack3_metrics_concate_all | 50 | 0.5 | 0.5 | 0.5185185185185185 | 0.5692729766803841 | 0.5
