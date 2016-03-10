#!/usr/bin/ksh
. ./project_setup.cfg

# Check for missing entries in dictionary XML
xmlErrors=$(for file in $(egrep -l "<suggestion>.*</suggestion>" $DATA/dict/sb_*.xml)
do
    basename $file | sed 's/sb_//g' | sed 's/.xml//g'
done | sort -u)

# Check for missing definitions
defnErrors=$(cat $DATA/spelling_bee_errors.log | grep "Missing Definition" | cut -d ':' -f 3 | egrep -v "^$" | sort -u)

# Check for missing audio
audioErrors=$(cat $DATA/spelling_bee_errors.log | grep "Missing Audio" | cut -d ':' -f 3 | egrep -v "^$" | sort -u)

# Check for audio mismatch
audioMatchErrors=$(cat $DATA/spelling_bee_errors.log | grep "Audio Mismatch" | cut -d ':' -f 3 | egrep -v "^$" | sort -u)

# Consolidate all errors (A)
allErrors=$(echo "${xmlErrors}"; echo "${defnErrors}"; echo "${audioErrors}"; echo "${audioMatchErrors}")
allErrors=$(echo "${allErrors}" | egrep -v "^$" | sort -u)
echo "$allErrors" > $DATA/sb_allErrors.tmp

# Check for resolved errors in override folder (B)
resolvedErrors=$(for file in $DATA/dict/override/sb_*.mp3
do
    basename $file | sed 's/sb_//g' | sed 's/.mp3//g'
done | sort -u
)
echo "$resolvedErrors" > $DATA/sb_resolvedErrors.tmp

# Determine unresolved errors (C = A - B)
comm -23 $DATA/sb_allErrors.tmp $DATA/sb_resolvedErrors.tmp > $DATA/sb_unresolvedErrors.tmp

# Retrieve complete word list (D)
cat $DATA/spelling_bee_2016-0*basic.txt | sort -u > $DATA/sb_allWords.tmp

# Exclude words not in the complete word list (E=C ∩ D)
comm -12 $DATA/sb_unresolvedErrors.tmp $DATA/sb_allWords.tmp > $DATA/sb_criticalErrors.tmp

# Determine words not in the complete word list (F=C - D)
comm -23 $DATA/sb_unresolvedErrors.tmp $DATA/sb_allWords.tmp > $DATA/sb_noncriticalErrors.tmp

echo ""
echo "A: Word definition and pronunciation errors:"
cat $DATA/sb_allErrors.tmp | column -x

echo ""
echo "B: Resolved errors:"
cat $DATA/sb_resolvedErrors.tmp | column -x

echo ""
echo "C: Unresolved errors (A - B):"
cat $DATA/sb_unresolvedErrors.tmp | column -x

echo ""
echo "E: Critical errors (C ∩ D, where D is the complete word list):"
cat $DATA/sb_criticalErrors.tmp | column -x

echo ""
echo "F: Non-Critical errors (C - D, where D is the complete word list):"
cat $DATA/sb_noncriticalErrors.tmp | column -x

rm -f $DATA/sb_allErrors.tmp
rm -f $DATA/sb_resolvedErrors.tmp
rm -f $DATA/sb_unresolvedErrors.tmp
rm -f $DATA/sb_allWords.tmp
rm -f $DATA/sb_criticalErrors.tmp
rm -f $DATA/sb_noncriticalErrors.tmp
