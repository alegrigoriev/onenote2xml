#!/usr/bin/sh

# Argument 1: versions directory (with .metadata file)
# Argument 2: Git repository
# Argument 3: branch name

versions_dir="$1"
git_dir="$2"
git_branch="$3"

if test -z "$versions_dir"
then
	echo "First argument (versions directory with .versions file) needs to be specified"
	exit 2
fi

versions_file="$versions_dir"/versions.txt
if ! test -f "$versions_file"
then
	echo "$versions_file file missing"
	exit 2
fi

if test -z "$git_dir"
then
	echo "Second argument (Git repository) needs to be specified"
	exit 2
fi

if ! test -d "$git_dir"
then
	echo "$git_dir directory missing"
	exit 2
fi

if test -z "$git_branch"
then
	echo "Third argument (Git branch) needs to be specified"
	exit 2
fi

if ! git -C "$git_dir" checkout --quiet --orphan "$git_branch"
then
	echo "Unable to create a new branch \"$git_branch\" in repository $git_dir"
	exit 2
fi

EMAIL="$(git -C "$git_dir" config --get user.email)"

git config --file "$versions_file" --get-regexp 'versions\.v.+' | {

	while read key datetime
	do
		# Replace "versions." prefix with "version."
		section=${key/#versions./version.}
		git config --file "$versions_file" --get-regexp "$section.+" | {
			TIMESTAMP=
			DIRECTORY=
			AUTHOR=

			while read key value
			do
				key=${key#$section.}
				# git config returns lower-cased keys
				if [ $key = author ]
				then
					AUTHOR="$value"
				elif [ $key = timestamp ]
				then
					TIMESTAMP="$value"
					GIT_DATE=$(date -d @$TIMESTAMP '+%s%z')
					PRETTY_DATE=$(date -d @$TIMESTAMP -R)
					echo "Section edited on $PRETTY_DATE by $AUTHOR"
				elif [ $key = directory ]
				then
					DIRECTORY="$value"
					export GIT_WORK_TREE="$(realpath "$versions_dir/$DIRECTORY")"
					# Git for Windows will skip files with timestamp with same seconds. Need to delete the old index
					(cd "$git_dir"; rm $(git rev-parse --git-path index) )
				fi
			done

			if test -z "$TIMESTAMP"; then echo "$section.TIMESTAMP missing"; exit 2; fi;
			if test -z "$AUTHOR"; then echo "$section.AUTHOR missing"; exit 2; fi;

			# Add machine-specific timezone to Git date:

			export GIT_COMMITTER_NAME="$AUTHOR"
			export GIT_COMMITTER_EMAIL="$EMAIL"
			export GIT_COMMITTER_DATE="$GIT_DATE"
			export GIT_AUTHOR_NAME="$AUTHOR"
			export GIT_AUTHOR_EMAIL="$EMAIL"
			export GIT_AUTHOR_DATE="$GIT_DATE"

			# Update the index
			git -C "$git_dir" -c core.safecrlf=false -c core.autocrlf=true add -- .
			git -C "$git_dir" commit --quiet -m "Edited by $AUTHOR on $PRETTY_DATE"
		}

	done
}
