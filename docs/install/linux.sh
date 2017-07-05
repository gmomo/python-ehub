#!/usr/bin/env bash
# This file is written in a literate programming way so that it can be run.
# This can ensure that this file is update to date with the code, if run
# periodically.

# First things first, you have to download the files.
git clone https://github.com/hues-platform/python-ehub.git

# This will put it into a directory called python-ehub
cd python-ehub

# If you already have GLPK or CPlex installed, you can skip these steps.  If
# you don't, I'll show you how to install glpk.

# First, we need to ensure we have the necessary stuff to install glpk.
sudo apt install wget build-essential

# Next, we create a folder to do the installation in
cd ..
mkdir glpk_install
cd glpk_install

# Now we download the GLPK files via FTP:
wget http://ftp.gnu.org/gnu/glpk/glpk-4.61.tar.gz

# and then extract them into our current directory
tar -zxvf glpk-4.61.tar.gz

cd glpk-4.61

# Now we go about installing GLPK.
# We first make sure all of GLPK's necessary stuff is set up
./configure

# We build the files
make

# Check that the files were correctly built
make check

# Install GLPK to the system
make install

# Clean up ourselves
make distclean

# Make sure Ubuntu (in this case) is happy
ldconfig

# and that's it for GLPK!

# Installing the Necessary Python files
# -------------------------------------

# If you have Python3.6 installed, the next step can be skipped.

# Here we install the programs that are necessary to run the Energy Hub Model:
sudo apt install python3-setuptools python3-wheel python3.6 python3-pip

# Now we switch back into `python-ehub`
cd ..
cd python-ehub

# Now that we have the programs to run the Energy Hub Model, we install all the
# libraries it uses:
python3.6 -m pip install -r requirements.txt

# That should install all the necessary libraries to run the Energy Hub Model.

# Congratulations, you've installed the Energy Hub Model!
