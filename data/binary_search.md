# Binary Search & Two Pointers — Principles, Templates & Pitfalls

## 1. Classical Binary Search
Used on monotonically sorted arrays or search spaces to locate a target element in $O(\log N)$ time.

### Invariant and Overflow-Safe Midpoint:
```python
def binary_search(nums, target):
    low, high = 0, len(nums) - 1
    while low <= high:
        mid = low + (high - low) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
```

### Lower Bound vs Upper Bound:
- **Lower Bound (`bisect_left`)**: First index `i` where `nums[i] >= target`.
- **Upper Bound (`bisect_right`)**: First index `i` where `nums[i] > target`.
```python
def lower_bound(nums, target):
    low, high = 0, len(nums)
    while low < high:
        mid = low + (high - low) // 2
        if nums[mid] < target:
            low = mid + 1
        else:
            high = mid
    return low
```

---

## 2. Binary Search on Answer (Monotonic Predicate)
When a problem asks for the "minimum maximum", "maximum minimum", or "smallest feasible value", check if the condition is monotonic:
`can_satisfy(x)` is `[False, False, True, True, True]` (find the first True), or
`can_satisfy(x)` is `[True, True, True, False, False]` (find the last True).

### Standard Template:
```python
def min_feasible_value(low_bound, high_bound):
    low, high = low_bound, high_bound
    ans = high
    while low <= high:
        mid = low + (high - low) // 2
        if is_feasible(mid):
            ans = mid         # Feasible, try to find a smaller one
            high = mid - 1
        else:
            low = mid + 1     # Not feasible, increase search value
    return ans
```

### Classic Problems:
1. **Koko Eating Bananas** (LeetCode 875): Search speed `[1, max(piles)]`, feasible if total hours $\le H$.
2. **Capacity To Ship Packages Within D Days** (LeetCode 1011): Search capacity `[max(weights), sum(weights)]`.
3. **Split Array Largest Sum** (LeetCode 410): Search max subarray sum.
4. **Aggressive Cows** / Magnetic Balls (LeetCode 1552): Search minimum distance between elements.

---

## 3. Two Pointers Techniques

### Pattern A: Opposite Ends (Converging Pointers)
Used when the array is sorted or symmetry exists.
- **Sorted Two Sum**: `left = 0, right = n - 1`. If `nums[left] + nums[right] < target`, `left++`; else `right--`.
- **Container With Most Water**: Area is `(right - left) * min(h[left], h[right])`. Greedily advance the pointer with the smaller height.
- **Trapping Rain Water**: Track `left_max` and `right_max`; advance whichever boundary is smaller.

### Pattern B: Fast and Slow Pointers (Floyd's Tortoise and Hare)
- Linked list cycle detection (return true if `slow == fast`).
- Finding middle of linked list (`fast` moves 2 steps, `slow` moves 1 step).
- Duplicate number in array of length $N+1$ with values in $[1, N]$.

---

## 4. Sliding Window (Subarrays and Substrings)

### Fixed Window Size $K$:
```python
def max_sum_subarray(nums, k):
    curr_sum = sum(nums[:k])
    max_sum = curr_sum
    for i in range(k, len(nums)):
        curr_sum += nums[i] - nums[i - k]
        max_sum = max(max_sum, curr_sum)
    return max_sum
```

### Variable Window Size (Dynamic Shrink & Expand):
General condition: Expand `right` until window violates invariant, then advance `left` to restore validity.
```python
def longest_valid_window(s):
    left = 0
    best = 0
    state = {}
    for right in range(len(s)):
        # 1. Add s[right] to state
        add(s[right], state)

        # 2. While window condition is violated, shrink from left
        while not is_valid(state):
            remove(s[left], state)
            left += 1

        # 3. Update best answer
        best = max(best, right - left + 1)
    return best
```
- Examples: Longest Substring Without Repeating Characters, Minimum Size Subarray Sum, Minimum Window Substring.
