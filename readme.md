About
=====

Distributed Reversi reinforcement learning of [AlphaGo zero](https://deepmind.com/blog/alphago-zero-learning-scratch/) and [Alpha Zero](https://arxiv.org/abs/1712.01815) methods.

- This [version](https://github.com/gooooloo/reversi-alpha-zero/tree/0.1) of code is verified capable to solve 4x4 Reversi Problem using **AlphaGoZero** way.
- This [version](https://github.com/gooooloo/reversi-alpha-zero/tree/0.2) of code is verified capable to train a rather strong 8x8 Reversi using **AlphaGoZero** way, which finally get a [NTest](https://github.com/weltyc/ntest) 10+ depth level. Detailed evaluation result is recorded [here](https://github.com/gooooloo/reversi-alpha-zero/blob/master/records.md#challenge-1).
- This [Version](https://github.com/gooooloo/reversi-alpha-zero/tree/0.3) of coded is verified capable to train a rather strong 8x8 Reversi using **AlphaZero** way, which finally get a [NTest](https://github.com/weltyc/ntest) 10+ depth level. Detailed evaluation result is recorded [here](https://github.com/gooooloo/reversi-alpha-zero/blob/master/records.md#challenge-3).


Environment
==========

* Ubuntu. I don't tested it on other OS platform.
* Python 3.6
* tensorflow-gpu: 1.3.0+
* Keras: 2.0.8


Implementation Architecture
==========
![](/images/pipeline.png)

Download Pretrained Model to Play with
==========

[Here](https://github.com/gooooloo/reversi-alpha-zero-models)


How to Train with AlphaZero Way
===============================


Suppose you having N(N>1) machines with GPU. You can use 1 for `opt` and
 `fs` module, and the other N-1 for `self` module. More specifically:

### On 1st GPU Machine
Run below command. It is for optimization module. This command will
consume all GPU resources. It loads play data and then train model, and
saves it as newest.

```bash
python3.6 -m src.reversi_zero.run opt --env reversi
```

Then run below command. It is for file server module (change 5678 to any
other port you like). It is necessary because self play is running on
other machines. This command doesn't need GPU. You need to figure out ip
of this machine, since it is needed when self playing on other machines.

```bash
python3.6 -m src.reversi_zero.run fs --env reversi --port 5678
```


### On Every Other N-1 GPU Machine
Let's say your machine running `fs` module is with ip 192.168.1.8, with
`--port 5678` arguments. And Let's say you have 8 CPU cores on this
machine, then you can run about 16 self play processes in parallel on
this machine. So you can run below command.

```bash
python3.6 -m src.reversi_zero.run self --env reversi --fs-url 192.168.1.8:5678 --n-workers 16
```

And you are done.


How to Train with AlphaGoZero Way
=================================

Suppose you having N(N>2) machines with GPU. You can use 1 for `opt` and
 `fs` module, 1 for `eval` module, and the other N-2 for `self` module.
 More specifically:

### On 1st GPU Machine
Run below command. It is for optimization module. This command will
consume all GPU resources. It loads play data and then train model, and
saves it as a candidate model.

```bash
python3.6 -m src.reversi_zero.run opt --env reversi --need-eval True
```

Then run below command. It is for file server module (change 5678 to any
other port you like). It is necessary because self play is running on
other machines. This command doesn't need GPU. You need to figure out ip
of this machine, since it is needed when self play on other machine. I
will assume it is 192.168.1.8 in this section for simplicity.

```bash
python3.6 -m src.reversi_zero.run fs --env reversi --port 5678
```


### On 2nd GPU Machine
Let's say you have 8 CPU cores on this machine, then you can run 4(=8/2)
evaluation games in parallel. So run below command. It is for evaluator
module. This command will consume all GPU resources. It loads latest
candidate model and current model, play between them, and replace
current model with candidate if the latter wins.

```bash
python3.6 -m src.reversi_zero.run eval --env reversi --fs-url http://192.168.1.8:5678 --n-workers 4
```


### On Every Other N-2 GPU Machine
Let's say you have 8 CPU cores per machine, then you can run about 16
self play processes in parallel per machine. And let's say you have 6GB
memory per machine, then you can use `model caching` feature with
10000000 entries to accelerate self play speed. So at last you can just
run below command.

```bash
python3.6 -m src.reversi_zero.run self --env reversi --fs-url http://192.168.1.8:5678 --n-workers 16 --model-cache-size 10000000
```

And you are done.


Advanced Options
================

Below are advanced options for usage. Check the codes for detailed usage
information (`src/reversi_zero/manager.py` would be a good entry point).


```
Option list description as a TODO
```


How to Manually Play Game with Trained Model
============================================

Let's say you have trained some model and you want to manually play with
it. You will need to run 2 modules at the same time: `http_server` as a
silent backend module running the model, and `play_gui` as a frontend
interacting with you. They can be run on different machines.
`http_server` uses GPU, while `play_gui` doesn't. They communicate via
HTTP request. More specifically:


### On 1st GPU Machine

Run below command. ( TODO: more options)

```bash
python3.6 -m src.reversi_zero.run http_server --env reversi --port 6543
```

### On 2nd CPU Machine

Make sure you installed pythonw. Let's say your 1st GPU machine is of
ip 192.168.31.9. Then run below command:

```bash
pythonw -m src.reversi_zero.run play_gui --env reversi --http-url http://192.168.31.9:6543
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

see [records.md](https://github.com/gooooloo/reversi-alpha-zero/blob/master/records.md) in this folder.

Credit
==========

- My codes are based on @mokemokechicken 's [original implementation](https://github.com/mokemokechicken/reversi-alpha-zero), which is really great.
- My multi-process idea is borrowed from @akababa 's [repo](https://github.com/Akababa/Chess-Zero).
