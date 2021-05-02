# set aliases
alias off="sudo poweroff"
alias py="sudo python"

export BASH_SOURCE=$(dirname "${BASH_SOURCE[0]}")
export REPO_PATH=`echo $BASH_SOURCE | grep -o '^.*projects'`
export REPO_NAME=`echo $BASH_SOURCE | sed 's/^.*projects\///g' | sed 's/\/.*//g'`


if [ -d "${REPO_PATH}/${REPO_NAME}" ] ; then
    
    export REPO_ROOT=${REPO_PATH}/${REPO_NAME}
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
	if [ -r "${REPO_ROOT}/${project}/project_setup.cfg" ] ; then
		echo ""
		echo "Switching to project ${project}."
		echo ""
		cd ${REPO_ROOT}/${project}
		. "${REPO_ROOT}/${project}/project_setup.cfg"
	fi
}

checkin() {
	gitRepo="$REPO_NAME"
	gitComment="$1"
	gitUser="$2"
	gitPwd="$3"

	cd $REPO_ROOT
	printf "\n**********  Git Status: Pre check-in  **********\n"
	git status

	printf "\n**********     Git Status: Commit     **********\n"
	git commit -m "${gitComment}"

	printf "\n**********      Git Status: Push      **********\n"
	git push "https://${gitUser}:${gitPwd}@github.com/${gitUser}/${gitRepo}.git" master

	printf "\n**********  Git Status: Post check-in **********\n"
	git status
	cd -
}

# spelling-bee project
proj spelling-bee

# electronics project
#proj electronics

echo ""
