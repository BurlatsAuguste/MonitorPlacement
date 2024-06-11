% Monitor Cover Problem
int: n; % number of nodes
int: r; % number of routes 
array[1..r,1..2] of int: routes_ends; % set of routes, contains index of starting and ending nodes of routes
array[1..r] of set of int: routes; % representation of routes, contains the set of nodes crossed by each route
array[1..n] of var bool:x; % monitors
array[1..r] of var bool:y; % measurement paths

% for a route to be a monitor path, its endpoints needs to be both monitors
constraint forall (path in 1..r) (y[path] <-> (x[routes_ends[path,1]] /\ x[routes_ends[path, 2]]));

% each node in the network needs to be covered by at least one measurement path
constraint forall (node in 1..n) (
  exists([y[path]| path in 1..r where (node in routes[path])]));

solve minimize(sum(x));

output ["nb monitors = \(sum(x))\n",
        "solution : \([i | i in 1..n where x[i]])\n"];