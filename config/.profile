# set aliases
alias off="sudo poweroff"
alias py="sudo python"

# define project functions
export PROJ_ROOT=/home/pi/projects/raspi

function proj {
	project="$1"
	echo ""
	echo "Switching to project ${project}."
	cd ${PROJ_ROOT}/${project}
	. ./project_setup.cfg
}

proj spelling-bee