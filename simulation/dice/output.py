#!/usr/bin/env python3

#
# output.py
# Author: Patrick Bannister
# Output and formatting for results of L7R dice Monte Carlo
# simulations.
#


class TextOutput:
  def __init__(self, stream, step=5, bins=15, delimiter='\t', show_mutator_value=True):
    self.stream = stream
    self.step = step
    self.bins = bins
    self.delimiter = delimiter
    self.show_mutator_value = show_mutator_value

  def header(self):
    bin_numbers = [i * self.step for i in range(1, self.bins)]
    header = '\t{}'.format('\t'.join([str(n) for n in bin_numbers]))
    if (self.show_mutator_value):
      header += '\tMutator Value'
    return header

  def format_simulation(self, simulation):
    '''
    format_simulation(simulation) -> str
      simulation (Simulation): a simulation that will be printed as a row

    Returns a delimited string showing the results of a simulation.
    '''
    # compute probabilities for each bin
    probabilities = []
    for i in range(1, self.bins):
      probabilities.append(sum(simulation.results[i:self.bins]) / simulation.trials)
    # format data
    label = '{}k{}'.format(simulation.rolled, simulation.kept)
    probabilities_str = self.delimiter.join(['{:.2f}'.format(p) for p in probabilities])
    fields = [label]
    fields.extend(['{:.2f}'.format(p) for p in probabilities])
    # Optionally include mutator value
    if (self.show_mutator_value):
      mutator_value = simulation.mutator_value / simulation.trials
      fields.append('{:.2f}'.format(mutator_value))
    # return delimited row
    return self.delimiter.join(fields)
 
  def write(self, simulations):
    '''
    write(simulations) -> str
      simulations (list of Simulation): simulations to format

    Returns a delimited string hat should be formatted
    '''
    simulations.sort()
    self.stream.write(self.header() + '\n')
    prev_rolled = 0
    for simulation in simulations:
      if (simulation.rolled != prev_rolled):
        self.stream.write('\n')
        prev_rolled = simulation.rolled
      self.stream.write(self.format_simulation(simulation) + '\n')
 
