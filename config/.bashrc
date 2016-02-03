# set aliases
alias off="sudo poweroff"
alias py="sudo python"

if [ -d "$HOME/projects/raspi" ] ; then
    export PROJ_ROOT=$HOME/projects/raspi
fi

# project navigation and maintenance
proj() {
	project="$1"
	if [ -r "${PROJ_ROOT}/${project}/project_setup.cfg" ] ; then
		echo ""
		echo "Switching to project ${project}."
		echo ""
		cd ${PROJ_ROOT}/${project}
		. "${PROJ_ROOT}/${project}/project_setup.cfg"
		ls
	fi
}

checkin() {
	gitProject="$1"
	gitComment="$2"

	cd $PROJ_ROOT
	git status
	git add *
	git commit -m "${gitComment}"
	git push "${gitProject}" master
	git status
	cd -
}

# spelling-bee project
proj spelling-bee

#alias sbp="ksh spelling_bee.ksh practice 2016"
#alias sbt="ksh spelling_bee.ksh test 2016"

alias sbs="sudo python spelling_bee.py study"
alias sbp="sudo python spelling_bee.py practice"
alias sbt="sudo python spelling_bee.py test"

echo ""
echo "Spelling Bee instructions:"
echo "To study   : sbs 2016 word lary-frees"
echo "To practice: sbp 2016-latin word lary-frees"
echo "To test    : sbt 2016-asian-languages-challenge chapter 1"
echo ""
echo "Lists available:"
ls -1 data/spelling_bee_*.txt | cut -d _ -f 3 | cut -d . -f 1 | column -x

# electronics project
#proj electronics

echo ""