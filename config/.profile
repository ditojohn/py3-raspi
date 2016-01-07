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

alias sbp="ksh spelling_bee.ksh practice 2016"
alias sbt="ksh spelling_bee.ksh test 2016"

echo "Spelling Bee instructions:"
echo "To practice: sbp word lary-frees"
echo "To test    : sbt chapter 1"
