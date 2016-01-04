# set aliases
alias off="sudo poweroff"
alias py="sudo python"

if [ -d "$HOME/projects/raspi" ] ; then
    export PRJ_ROOT=$HOME/projects/raspi
fi

prj() {
	project="$1"
	if [ -r "${PRJ_ROOT}/${project}/project_setup.cfg" ] ; then
		echo ""
		echo "Switching to project ${project}."
		echo ""
		cd ${PRJ_ROOT}/${project}
		. "${PRJ_ROOT}/${project}/project_setup.cfg"
	fi
}

prj spelling-bee