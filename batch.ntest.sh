log=/tmp/batch.ntest.sh.result.log
echo '' > $log
for ndepth in `echo 10 11 12 13 14 15 16`; do
	for nsteps in `echo 453800 451400`; do
		#for nsims in `echo 30`; do
		#	cmd=`echo python -m src.reversi_zero.run elo_p1_ntest --env reversi --n-workers 2 --n-games 4 --ntest-depth $ndepth --n-minutes $nsims --n-steps-model $nsteps --save-versus-dir ./data/reversi/ggf/`
		for nsims in `echo 100 400 800`; do
			cmd=`echo python -m src.reversi_zero.run elo_p1_ntest --env reversi --n-workers 10 --n-games 10 --ntest-depth $ndepth --n-sims $nsims --n-steps-model $nsteps --save-versus-dir ./data/reversi/ggf/`
			echo $cmd
			echo $cmd >> $log
			eval $cmd >> $log
		done
	done
done

echo check out $log for result!
