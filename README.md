You should be able to follow these lectures (and execute the examples) on your laptop or on Adroit. On Adroit, we will *not* do `salloc` to reserve an instance and therefore everyone will work on the head node under the same user account. Use your laptop if you can.

# Dependencies (for your laptop)

To follow these lectures and execute the examples, you'll need

   * Jupyter with Python 2.7
   * Scala (for the third notebook)

I recommend installing Jupyter through Miniconda. Follow [these instructions](https://conda.io/docs/install/quick.html) to install Miniconda (*with Python 2.7, not 3.5!*) and then

```bash
conda install jupyter
```

For Scala, we can install a Jupyter-Scala notebook extension and it will get Scala as a dependency.

```bash
wget https://github.com/alexarchambault/jupyter-scala/archive/v0.4.2.tar.gz
tar -xzvf v0.4.2.tar.gz
cd jupyter-scala-0.4.2
./jupyter-scala
jupyter console --kernel scala
cd ..
```

I also use [RISE](https://github.com/damianavila/RISE) to make the notebook look like slides, but you don't have to.

# Starting the notebook (on your laptop)

Get a copy of the repository, either by

```bash
git clone https://github.com/jpivarski/codas-functional-programming.git
```

or by

```bash
wget https://github.com/jpivarski/codas-functional-programming/archive/presented-2017-07-10.tar.gz
tar -xzvf presented-2017-07-10.tar.gz
```

Step into this directory and start Jupyter

```bash
cd codas-functional-programming*
jupyter notebook
```

This will open a Jupyter tab in your web browser. In this tab, click on `nb1-introduction.ipynb`.

# Starting the notebook (on Adroit)

In the lecture itself, I should have already started a notebook. In that case, log into Adroit using the username and password you were given, and the following ssh command:

```bash
ssh -Llocalhost:54321:localhost:8888 username@password
```

The "`54321`" is arbitrary, so pick a different one if your laptop is already using this port.

After ssh is connected, go to your web browser and connect to "`localhost:54321`" (or whatever port you've forwarded it to). It will prompt you for a password that I'll give you, and then you can click on `nb1-introduction.ipynb`.
