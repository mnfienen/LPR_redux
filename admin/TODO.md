0. make a version of pycap where a single table of Q can drive the calculations
1. in comparing MODFLOW with `pycap` we can:  
    - compare water balance components
    - calculate depletion potential for a single well with both and compare
2. Make histograms of receipts for each pareto solution in the cashmoney version
    - show how to dereference all the data from a single pareto solution and have them plot it in various ways
3. show all the new pareto curves in Q vs. depletion units (e.g. the first plot.). Can't reverse calculate depletion from fish prob. but use the wells and run `pycap`
4. make it so students can plot their own solutions
5. Modularize setting up MOU runs for the students
6. for the modflow/pycap comps
    - allow for variable to select a well from DP to evaluate (provide a valid list)
    - choose your own adventure -- either completed version all through to DP, or work to do
    - for the open-ended option, only leave them the need to manipulate well file