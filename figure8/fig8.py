import numpy as np
from scipy import sparse
from scipy.integrate import odeint
import matplotlib.pyplot as plt
import math as mt
from stimulus import *
from myintegrator import *
import cProfile
import json
import matplotlib.gridspec as gridspec
import cPickle as pickle

# this is the transfer function 
def phi(x,theta,uc):
	myresult=nu*(x-theta)
	myresult[x<theta]=0.
	myresult[x>uc]=nu*(uc-theta)
	return myresult

def phi_tanh(x):
	return 0.5*(1+np.tanh(a1*(x+b1)))

#def mytauInv(x): #time scale function synapses
#	myresult=np.zeros(len(x))
#	myresult[x>thres]=1/tau_learning
#	return myresult
def mytau(x): #time scale function synapses
	myresult=(1e50)*np.ones(len(x))
	myresult[x>thres]=tau_learning
	#print x>thres
	#print x
	#myresult=(1e8)*(1.+np.tanh(-50.*(x-thres)))+tau_learning
	#print myresult
	return myresult


def winf(x_hist):
	pre_u=phi(x_hist[0],theta,uc)
	post_u=phi(x_hist[-1],theta,uc)
	#parameters
	n=len(pre_u)
	vec_pre=0.5*(np.ones(n)+np.tanh(a_pre*(pre_u-b_pre)))
	return (wmax/2.)*np.outer((np.ones(n)+np.tanh(a_post*(post_u-b_post))),vec_pre)

#function for the field
#x_hist is the 'historic' of the x during the delay period the zero is the oldest and the -1 is the newest

def tauWinv(x_hist):
	pre_u=phi(x_hist[0],theta,uc)
	post_u=phi(x_hist[-1],theta,uc)

	tau_inv =   np.add.outer(1/mytau(post_u),1/mytau(pre_u))
	tau_inv[tau_inv == 2. / tau_learning] = 1./tau_learning
	return tau_inv
	#return tau_learning*np.outer(1./mytau(post_u),1./mytau(pre_u))

def F(u):
	return .5*(1.+np.tanh(af*(u-bf)))

def field(t,a,x_hist,W,H):
	pre_u=x_hist[0]
	post_u=x_hist[-1]
	n=len(pre_u)
	conn_matrix=(W.T*H).T
	field_u=(1/tau)*(mystim.stim(t)+conn_matrix.dot(phi(x_hist[-1],theta,uc))-x_hist[-1]-w_inh*np.dot(r1_matrix,phi(x_hist[-1],theta,uc)))#-a
	field_a=0.#in the paper we are not using adaptation during learning
	field_H=(H*(1.-(phi(post_u,theta,uc)/y0))-H**2)/tau_H
	field_w=np.multiply(tauWinv(x_hist),winf(x_hist)-W)
	return field_a,field_u,field_w,field_H

#This are a the parameters of the simulation

#open parameters of the model
n=10 #n pop
delay=15.3
tau=10.   #timescale of populations
tau_H=20000#2000.#200000.
af=0.1
bf=0.
y0=.05*np.ones(n)
w_i=4.3
w_inh=w_i/n
nu=1.
theta=0.
uc=1.
wmax=3.5#HERE 1.45#1.6#2.2#1.6
thres=0.6
beta=1.6
tau_a=10.
#parameters stimulation
dt=0.5
lagStim=400.
times=285#HERE! 235
amp=5.4#HERE!#3.5


delta=7.#30#7.
period=14.#25#14.

bf=10.
xf=0.7
a_post=bf
b_post=xf
a_pre=bf
b_pre=xf
tau_learning=400.#30000.

a1=6.
b1=-0.25


#-------------------------------------------------------------------
#-----------------Stimulation of Populations------------------------
#-------------------------------------------------------------------

# settin`g up the simulation 

r1_matrix=np.ones((n,n))
patterns=np.identity(n)
patterns=[patterns[:,i] for i in range(n)]
mystim=stimulus(patterns,lagStim,delta,period,times)
mystim.inten=amp

#integrator
npts=int(np.floor(delay/dt)+1)         # points delay
tmax=times*(lagStim+n*(period+delta))+100.+mystim.delay_begin
thetmax=tmax+30*tau_H


#initial conditions
a0=np.zeros((npts,n))
x0=0.01*np.ones((npts,n))
W0=[0.1*np.ones((n,n)) for i in range(npts)]
H0=[0.5*np.ones(n) for i in range(npts)]
theintegrator=myintegrator(delay,dt,n,thetmax)
theintegrator.fast=False
adapt,u,connectivity,WLast,myH,t=theintegrator.DDE_Norm_Miller(field,a0,x0,W0,H0)

pickle.dump((u,connectivity,myH,t),open('dyn_stimulation.p','wb'))

#-----------------------------------------------------------------------------------------
#-------------------------------- Dynamics-----------------------------------------------
#----------------------------------------------------------------------------------------

#initial conditions

tmaxdyn=500
mystim.inten=0.
a0=np.zeros((npts,n))
x0=0.01*np.ones((npts,n))
x0[:,0]=1.
W0=[connectivity[-1] for i in range(npts)]
H0=[myH[-1] for i in range(npts)]
theintegrator=myintegrator(delay,dt,n,tmaxdyn)
theintegrator.fast=False
adapt_ret,u_ret,connectivity_ret,WLast_ret,myH_ret,t_ret=theintegrator.DDE_Norm_Miller(field,a0,x0,W0,H0)

plt.plot(t_ret,u_ret)
plt.show()
#pickle.dump((u_ret,connectivity_ret,myH_ret,t_ret),open('dyn_retrieval_PA.p','wb'))
pickle.dump((u_ret,connectivity_ret,myH_ret,t_ret),open('dyn_retrieval.p','wb'))






