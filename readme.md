About
=====

Reversi reinforcement learning of [AlphaGo zero](https://deepmind.com/blog/alphago-zero-learning-scratch/) and [Alpha Zero](https://arxiv.org/abs/1712.01815) methods.


Environment
-----------

* Ubuntu / OSX. I don't tested it in Windows.
* Python 3.6
* tensorflow-gpu: 1.3.0+
* Keras: 2.0.8


Download Pretrained Model to Play with
==========

[Here](https://github.com/gooooloo/reversi-alpha-zero-models)


Training Pipeline Examples
==========

Below are some examples for usage. Check the codes for detailed usage information (`src/reversi_zero/manager.py` would be a good entry point).


Self-Play
--------

```bash
python3.6 -m src.reversi_zero.run self --env reversi
```
```bash
python3.6 -m src.reversi_zero.run self --env reversi --n-workers 4 
```
```bash
python3.6 -m src.reversi_zero.run self --env reversi --n-workers 4 --gpu-memory-frac 0.8
```
```bash
python3.6 -m src.reversi_zero.run self --env reversi --n-workers 4 --can-resign False
```

Maintaining resignation threshold
-------

```bash
# Required for self play in my enrivonment. Maybe you don't need it.
python3.6 -m src.reversi_zero.run res --env reversi
```

Trainer
-------

```bash
# AlphaZero style
python3.6 -m src.reversi_zero.run opt --env reversi
```

```bash
# AlphaGoZero style
python3.6 -m src.reversi_zero.run opt --env reversi  --need-eval True
```

Evaluator
---------

```bash
python3.6 -m src.reversi_zero.run eval
```

```bash
python3.6 -m src.reversi_zero.run eval --n-workers 4
```

Play Game Examples
==========

Start Http Server
---------

```bash
# use best model
python3.6 -m src.reversi_zero.run http_server --env reversi
```
```bash
# have a chance to select specific generation of model from console
python3.6 -m src.reversi_zero.run http_server --env reversi --ask-model true
```
```bash
# specify simulations per move
python3.6 -m src.reversi_zero.run http_server --env reversi --n-sims 100
```
```bash
# use the specific generation of model
python3.6 -m src.reversi_zero.run http_server --env reversi --n-steps-model 424000
```
```bash
# set the http port
python3.6 -m src.reversi_zero.run http_server --env reversi --http-port 8888
```


Play GUI
---------

```bash
python3.6 -m src.reversi_zero.run play_gui --env reversi
```
```bash
# show local GUI, but the model run on another server.
pythonw -m src.reversi_zero.run play_gui --env reversi --http-url http://192.168.31.9:8888
```

Play with NTest
---------

[NTest](https://github.com/weltyc/ntest) is a very strong Reversi AI. We can play with it automatically. Just modify `batch.ntest.sh` and run.

```bash
. ./batch.ntest.sh
```

Play between different generations of model
---------

Sometimes I want to compete strength of different models. So I setup the models in `src/reversi_zero/worker/league.py` and run.

```bash
python3.6 -m src.reversi_zero.run league --env reversi --n-workers 4
```


Strength Records
==========

Below records are using the AlphaGoZero way,  which has a 'Evaluator' module. Not AlphaZero way.

Records 1
---------

Rule: Play with this [iOS APP](https://itunes.apple.com/cn/app/id574915961). For each model, we plays 2 games, 1 as black, 1 as white. If wins at least once, no matter as black or white, we count it as a 'won'.

- step-17600 (100sim): won level 1,2,3
- step-20000 (100sim): won level 4
- step-28000 (100sim): won level 5,6,7,8,9,10
- step-40000 (100sim): won level 11
- step-42400 (100sim): won level 12
- step-52000 (100sim): won level 16
- step-54400 (100sim): won level 14,15
- step-56800 (100sim): won level 13
- step-64800 (100sim): lose level 17...
- step-67200 (100sim): lose level 17...
- step-69600 (100sim): lose level 17...
- step-69600 (2000sim): won level 17 (level 18 not tested)
- step-116000 (2000sim): won level 18,19,20,21,22,23,24,25,26,27,28,29,30
- step-116000 (800sim): lose level 29
- step-155200 (2000sim): won level 32 (level 33 not tested)
- step-200800 (800sim): won level 33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50 (level 51 not tested)
- step-200800 (200sim): lose level 51...
- step-200800 (400sim): won level 51,52,53,54,55,56,57,58,59,60,61

(then I lose my record in game. Have to restart ...)

Records 2
---------

Rule: Play with this [iOS APP](https://itunes.apple.com/ca/app/id574915961). For each model, we plays 2 games, 1 as black, 1 as white. If wins at least once, no matter as black or white, we count it as a 'won'.

Model step-350400 can be downloaded from [here](https://github.com/gooooloo/reversi-alpha-zero-models/tree/master/model_350400-steps)

- step-263200 (100sim): won level ~ 31, lose to level 32
- step-302400 (100sim): won level ~ 44 (level 45 not tested yet)
- step-302400 (40sim): won level ~ 53, lose to level 54 
- step-314400 (40sim): won level ~ 54, lose to level 55
- step-314400 (100sim): won level ~ 58, lose to level 59
- step-314400 (200sim): won level ~ 59, lose to level 60
- step-314400 (400sim): won level ~ 97, lose to level 98
- step-350400 (100sim): won level 98, lose to level 99
- step-350400 (400sim): lose to level 99
- step-350400 (800sim): won level 99

Records 3
---------

Rule: play with NTest. `NTest:xxx` means NTest with strenth xxx. 

For simplicity, a blank cell means losing ALL 20 games, and a '-' means not tested.

|           |        |  NTest:10  |  NTest:11  |  NTest:12  |  NTest:13  |
|-----------|-------:|:----------:|:----------:|:----------:|:----------:|
|step-386400| 100 sim|            |            |            |            |
|           | 200 sim|            |   0/ 2/18  |            |            |
|           | 400 sim|   0/ 3/17  | **0/20/ 0**|            |            |
|           | 800 sim|            | **0/20/ 0**|            |            |
|step-391200| 100 sim|            |            |            |            |
|           | 200 sim|            |            |            |            |
|           | 400 sim|            |            |            |            |
|           | 800 sim|            |   0/ 1/19  |   5/ 0/15  |   5/ 0/15  |
|step-401600| 100 sim|            |            |            |            |
|           | 200 sim|            |            |            |            |
|           | 400 sim|            |            |   0/ 4/16  |            |
|           | 800 sim|            |            |            |            |
|step-406400| 100 sim|            |            |            |            |
|           | 200 sim|            |            |            |            |
|           | 400 sim|            | **0/19/ 1**|   1/ 0/19  |   0/ 1/19  |
|           | 800 sim|            |            |   0/ 7/13  |   0/12/ 8  |
|step-421600| 100 sim|            |            |            |            |
|           | 200 sim|   2/ 0/18  |            |            |            |
|           | 400 sim|**20/ 0/ 0**| **0/20/ 0**|            |            |
|           | 800 sim|   3/ 0/17  | **0/20/ 0**|            |            |
|step-424000| 100 sim|            |            |            |            |
|           | 200 sim|   0/ 2/18  |            |   2/ 0/18  |            |
|           | 400 sim|**20/ 0/ 0**| **0/20/ 0**|   8/ 0/12  |            |
|           | 800 sim|**12/ 0/ 8**|      -     |   2/ 0/18  |            |
|           |1600 sim|   1/ 0/19  |      -     |      -     |      -     |
|           |3200 sim|   3/ 0/17  |      -     |      -     |      -     |
|           |6400 sim|   5/ 0/15  |      -     |      -     |      -     |
|step-440000| 100 sim|            |            |      -     |      -     |
|           | 200 sim|            |            |      -     |      -     |
|           | 400 sim| **9/ 2/ 9**|            |      -     |      -     |
|           | 800 sim|**10/ 0/10**|            |      -     |      -     |
|step-442500| 100 sim|            |            |            |            |
|           | 200 sim|            |            |            |            |
|           | 400 sim|**16/ 0/ 4**|            |            |            |
|           | 800 sim|**19/ 0/ 1**|   0/ 5/15  |            |            |
|step-444900| 100 sim|            |            | **0/20/ 0**|            |
|           | 200 sim|            |            | **0/20/ 0**|            |
|           | 400 sim|   1/ 0/19  |   0/ 3/17  |   0/13/ 7  |            |
|           | 800 sim|   7/ 1/12  |   0/ 5/15  |   0/11/ 9  |            |
|step-447300| 100 sim|      -     |            |            |      -     |
|           | 200 sim|      -     |            |            |      -     |
|           | 400 sim|      -     |            |            |      -     |
|           | 800 sim|      -     |            |            |      -     |
|step-450500| 100 sim|      -     |            |            |      -     |
|           | 200 sim|      -     |            |            |      -     |
|           | 400 sim|      -     |   1/ 2/17  |            |      -     |
|           | 800 sim|      -     | **0/19/ 1**|            |      -     |


Credit
==========

- My codes are based on @mokemokechicken 's [original implementation](https://github.com/mokemokechicken/reversi-alpha-zero), which is really great.
- My multi-process idea is borrowed from @akababa 's [repo](https://github.com/Akababa/Chess-Zero).
