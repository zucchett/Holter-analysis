#/bin/bash

# usage: source runRdsamp.sh DIRECTORYWITHBINARYDATA
# example: source runRdsamp.sh 1/

# set here maximum number of seconds of data taking
option="-l 100"
option=""

direcname=$1

for rawfile in $(ls $dirname/*RawData.bin); do
	# Extract the file number (correspinding to the hour)
	rawname=$(basename $rawfile)
	direcname=$(dirname $rawfile)
	rawnumber=${rawname//[!0-9]/}
	name="Hour"$rawnumber
	outname=$direcname/Hour"$rawnumber"UnpackedData.csv
	echo Unpacking binary file $direcname/$rawname [file number $rawnumber]
	# Prepare the header file and edit it
	cp header.hea $name.hea
	sed -i '' 's/NAME/'$name'/g' $name.hea
	sed -i '' 's/FILE/'$rawname'/g' $name.hea
	sed -i '' 's/DIRECTORY/'$direcname'/g' $name.hea
	# Run rdsamp
	rdsamp -r $name.hea -c -P -H $option > $outname
	echo Wrote output file $outname [size $(du -h $outname | awk '{print $1}')]
	# Clean
	rm $name.hea
done