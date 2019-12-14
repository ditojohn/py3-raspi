# set aliases
alias off="sudo poweroff"
alias py="sudo python"

if [ -d "$HOME/projects/raspi" ] ; then
    export PROJ_ROOT=$HOME/projects/raspi
fi

# file maintenance
backup() {
	for file in $@
	do
		mv ${file} ${file}.$(date +%Y%m%d%H%M%S).bkp
        rc=$?

        if [ ${rc} -eq 0 ] ; then
            echo "Backed up file ${file} to ${file}.$(date +%Y%m%d%H%M%S).bkp"
        else
            echo "ERROR: Unable to back up file ${file}"
        fi      
	done
}

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

# electronics project
#proj electronics

echo ""
