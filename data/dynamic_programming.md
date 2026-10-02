# Dynamic Programming (DP) — Patterns, Intuition & Cheatsheet

## 1. What is Dynamic Programming?
Dynamic Programming is an algorithmic optimization technique that solves complex problems by breaking them down into simpler subproblems, solving each subproblem only once, and storing their solutions (memoization or tabulation) to avoid redundant recalculation.

### Core Requirements:
1. **Optimal Substructure**: The optimal solution to the problem can be constructed from the optimal solutions to its subproblems.
2. **Overlapping Subproblems**: The same subproblems are encountered repeatedly during recursion.

---

## 2. Top-Down (Memoization) vs Bottom-Up (Tabulation)

| Aspect | Top-Down (Memoization) | Bottom-Up (Tabulation) |
|---|---|---|
| **Approach** | Starts from original problem; recurses down. | Starts from base cases; iterates up. |
| **Data Structure** | Hash map or array cache + recursion. | Table (1D, 2D, or N-D array) + loops. |
| **Pros** | Only computes required subproblems; easy to translate from recursive intuition. | Eliminates recursion stack overhead; easy space optimization. |
| **Cons** | Stack overflow risk for large recursion depths ($N > 10^4$). | May compute subproblems that are not strictly necessary. |

---

## 3. The 5-Step Framework to Solve Any DP Problem
1. **Define the State**: What do the parameters represent? (e.g., `dp[i][w]` is the max value using a subset of the first `i` items with max weight `w`).
2. **Determine the Base Cases**: What are the simplest boundary conditions that can be solved immediately without subproblems? (e.g., `dp[0] = 0`, `dp[1] = 1`).
3. **Derive the Recurrence Relation**: How does the answer for the current state depend on smaller previous states? What decision/choice are you making at step $i$?
4. **Determine the Computation Order**: In what order must the table be filled so that dependencies are already resolved?
5. **Space Optimization (Optional)**: If `dp[i]` only depends on `dp[i-1]`, reduce the space from $O(N \times W)$ to $O(W)$ using 1D rolling arrays.

---

## 4. Classic DP Patterns

### Pattern 1: 0/1 Knapsack vs Unbounded Knapsack
- **0/1 Knapsack** (Each item can be picked at most once):
  - Recurrence: `dp[i][w] = max(dp[i-1][w], dp[i-1][w - weight[i]] + value[i])`
  - Space-optimized 1D array trick: Iterate weight **backwards** (from `W` down to `weight[i]`) so you don't use the same item multiple times in the same pass:
    ```python
    dp = [0] * (capacity + 1)
    for w_i, v_i in items:
        for w in range(capacity, w_i - 1, -1):
            dp[w] = max(dp[w], dp[w - w_i] + v_i)
    ```
- **Unbounded Knapsack** (Items can be reused infinitely, e.g., Coin Change):
  - Recurrence: `dp[w] = min(dp[w], dp[w - coin] + 1)`
  - Space-optimized 1D array trick: Iterate weight **forwards** (from `coin` up to `W`).

### Pattern 2: Longest Common Subsequence (LCS) & Edit Distance
- **LCS**:
  - If `s1[i-1] == s2[j-1]`: `dp[i][j] = 1 + dp[i-1][j-1]`
  - Else: `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`
- **Edit Distance (Levenshtein)**:
  - If `s1[i-1] == s2[j-1]`: `dp[i][j] = dp[i-1][j-1]`
  - Else: `dp[i][j] = 1 + min(insert: dp[i][j-1], delete: dp[i-1][j], replace: dp[i-1][j-1])`

### Pattern 3: Longest Increasing Subsequence (LIS)
- **Standard $O(N^2)$ DP**: `dp[i] = 1 + max(dp[j] for j < i if nums[j] < nums[i])`
- **Optimal $O(N \log N)$ Patience Sorting + Binary Search**:
  - Maintain a list `tails` where `tails[i]` stores the smallest tail element of all increasing subsequences of length `i + 1`.
  - For each number `x`, use `bisect_left(tails, x)` to replace or append.

### Pattern 4: Interval DP
- Subproblems represent continuous subarrays `[i, j]`.
- Loop over interval lengths from `len = 2` up to `N`.
- Example problems: Matrix Chain Multiplication, Burst Balloons, Stone Game.
- Template:
  ```python
  for length in range(2, n + 1):
      for i in range(n - length + 1):
          j = i + length - 1
          for k in range(i, j):
              dp[i][j] = min(dp[i][j], dp[i][k] + dp[k+1][j] + cost(i, k, j))
  ```

### Pattern 5: Bitmask DP
- Used when $N \le 20$. A bitmask integer represents the subset of visited vertices or selected elements.
- Example problems: Traveling Salesperson Problem (TSP), Assigning Tasks to Workers.
- Transitions iterate over all submasks or turn on the $k$-th bit: `mask | (1 << k)`.

---

## 5. Constraint Guide for DP
- $N \le 20$: Bitmask DP ($O(2^N \cdot N)$ or $O(3^N)$)
- $N \le 400$: $O(N^3)$ (Interval DP, Floyd-Warshall)
- $N \le 2000$: $O(N^2)$ (2D DP, Knapsack, LCS, Matrix DP)
- $N \le 10^5$: $O(N)$ or $O(N \log N)$ (1D DP, Monotonic Queue DP, Segment Tree DP)
