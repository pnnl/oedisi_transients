# OEDISI Transients Algorithm

## Use-Case Development

The transient use case is split into two steps: 

a. Dataset generation 

Dataset generation within the transient use case provide sufficient training/validation dataset for the follow-up transient analysis algorithms. To obtain the dataset from a specific test model with certain level of PV penetration, the user will first pick a model in ATP format from the OEDI repository. The test model originates with different steady state settings, including the loading condition and PV capacity, which forms multiple ATP net files. Then the user has the option to modify the transient state settings or not. If so, the transient state settings will be edited under the user’s local workstation. After all the scenarios are designed and prepared, the ATP simulation will generate the datasets in the corresponding ATP format. Lastly, the user has to implement data processing step and then output the required data formats.

b. Event detection and identification algorithms.
