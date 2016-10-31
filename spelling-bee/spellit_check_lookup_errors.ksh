#!/usr/bin/ksh
. ./project_setup.cfg

# Check for missing entries in dictionary XML
for file in $(egrep -l "<suggestion>.*</suggestion>" $DATA/dict/sb_*.xml)
do
    basename $file | sed 's/sb_//g' | sed 's/.xml//g'
done > $DATA/sbe_xmlErrors.tmp

# Check for resolved definition errors in override folder (B1)
for file in $DATA/dict/override/sb_*.dat
do
    basename $file | sed 's/sb_//g' | sed 's/.dat//g'
done | sort -u > $DATA/sbe_resolvedDefnErrors.tmp

# Check for resolved pronunciation errors in override folder (B2)
for file in $DATA/dict/override/sb_*.mp3
do
    basename $file | sed 's/sb_//g' | sed 's/.mp3//g'
done | sort -u > $DATA/sbe_resolvedPronErrors.tmp

echo "-----------------------------------------------------------------------------"
echo "Resolved Errors"
echo "-----------------------------------------------------------------------------"
echo ""
echo "B1: Resolved word definition errors:"
cat $DATA/sbe_resolvedDefnErrors.tmp | column -x
echo ""
echo "B2: Resolved word pronunciation errors:"
cat $DATA/sbe_resolvedPronErrors.tmp | column -x

###################################################################################
# Check for missing word definition errors
###################################################################################

# Check for missing definitions from error log
cat $DATA/log/spelling_bee_errors.log | grep "Missing Definition" | cut -d ':' -f 3 | egrep -v "^$" > $DATA/sbe_logErrors.tmp

# Consolidate definition errors (A)
cat $DATA/sbe_xmlErrors.tmp $DATA/sbe_logErrors.tmp | sort -u > $DATA/sbe_allErrors.tmp

# Determine unresolved definition errors (C = A - B1)
comm -23 $DATA/sbe_allErrors.tmp $DATA/sbe_resolvedDefnErrors.tmp > $DATA/sbe_unresolvedErrors.tmp

echo ""
echo "-----------------------------------------------------------------------------"
echo "Missing Word Definition Errors"
echo "-----------------------------------------------------------------------------"
echo ""
echo "A: All errors:"
cat $DATA/sbe_allErrors.tmp | column -x
echo ""
echo "C: Unresolved errors (A - B1):"
cat $DATA/sbe_unresolvedErrors.tmp | column -x

###################################################################################
# Check for missing word pronunciation errors
###################################################################################

# Check for missing pronunciations from error log
cat $DATA/log/spelling_bee_errors.log | grep "Missing Audio" | cut -d ':' -f 3 | egrep -v "^$" > $DATA/sbe_logErrors.tmp

# Consolidate pronunciation errors (A)
cat $DATA/sbe_xmlErrors.tmp $DATA/sbe_logErrors.tmp | sort -u > $DATA/sbe_allErrors.tmp

# Determine unresolved pronunciation errors (C = A - B2)
comm -23 $DATA/sbe_allErrors.tmp $DATA/sbe_resolvedPronErrors.tmp > $DATA/sbe_unresolvedErrors.tmp

echo ""
echo "-----------------------------------------------------------------------------"
echo "Missing Word Pronunciation Errors"
echo "-----------------------------------------------------------------------------"
echo ""
echo "A: All errors:"
cat $DATA/sbe_allErrors.tmp | column -x
echo ""
echo "C: Unresolved errors (A - B2):"
cat $DATA/sbe_unresolvedErrors.tmp | column -x

###################################################################################
# Check for word pronunciation mismatch errors
###################################################################################

# Check for pronunciation mismatch from error log
cat $DATA/log/spelling_bee_errors.log | grep "Audio Mismatch" | cut -d ':' -f 3 | egrep -v "^$" > $DATA/sbe_logErrors.tmp

# Consolidate pronunciation errors (A)
cat $DATA/sbe_logErrors.tmp | sort -u > $DATA/sbe_allErrors.tmp

# Determine unresolved pronunciation errors (C = A - B2)
comm -23 $DATA/sbe_allErrors.tmp $DATA/sbe_resolvedPronErrors.tmp > $DATA/sbe_unresolvedErrors.tmp

echo ""
echo "-----------------------------------------------------------------------------"
echo "Word Pronunciation Mismatch Errors"
echo "-----------------------------------------------------------------------------"
echo ""
echo "A: All errors:"
cat $DATA/sbe_allErrors.tmp | column -x
echo ""
echo "C: Unresolved errors (A - B2):"
cat $DATA/sbe_unresolvedErrors.tmp | column -x

# Check for manual / forced overrides

echo ""

#######################################################################################
# Cleanup
#######################################################################################

rm -f $DATA/sbe_*.tmp

#######################################################################################

