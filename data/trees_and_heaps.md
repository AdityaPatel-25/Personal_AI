# Trees, Binary Search Trees & Heaps — Core Concepts & Templates

## 1. Tree Traversals
- **Preorder** (Root, Left, Right): Useful for serialization, cloning trees.
- **Inorder** (Left, Root, Right): For BST, produces strictly non-decreasing sorted order.
- **Postorder** (Left, Right, Root): Bottom-up processing (e.g., tree height, diameter, deleting nodes).
- **Level-order (BFS)**: Breadth-first level-by-level using a `collections.deque`.

---

## 2. Lowest Common Ancestor (LCA)

### In Binary Search Tree (BST) — $O(H)$ time:
```python
def lowestCommonAncestorBST(root, p, q):
    curr = root
    while curr:
        if p.val > curr.val and q.val > curr.val:
            curr = curr.right
        elif p.val < curr.val and q.val < curr.val:
            curr = curr.left
        else:
            return curr  # Split point is LCA
```

### In General Binary Tree — $O(N)$ time:
```python
def lowestCommonAncestor(root, p, q):
    if not root or root == p or root == q:
        return root
    left = lowestCommonAncestor(root.left, p, q)
    right = lowestCommonAncestor(root.right, p, q)
    if left and right:
        return root  # p and q found in separate subtrees
    return left or right
```

---

## 3. Tree Diameter & Maximum Path Sum
Key insight: At every node `u`, calculate:
1. The maximum path passing through `u` that combines left and right branches (updates global answer).
2. The maximum single-branch path starting at `u` extending downwards (returns to parent).

```python
def maxPathSum(root):
    max_sum = float('-inf')

    def dfs(node):
        nonlocal max_sum
        if not node:
            return 0
        left_gain = max(dfs(node.left), 0)
        right_gain = max(dfs(node.right), 0)

        # Path through this node
        max_sum = max(max_sum, node.val + left_gain + right_gain)

        # Return max single branch
        return node.val + max(left_gain, right_gain)

    dfs(root)
    return max_sum
```

---

## 4. Heaps & Priority Queues

### Python `heapq` Cheatsheet:
- Python implements a **min-heap** by default.
- To use as a **max-heap**, negate values: `heapq.heappush(max_heap, -val)` and read `-heapq.heappop(max_heap)`.
- Heapify an existing list: `heapq.heapify(nums)` in $O(N)$ linear time.
- Push and pop: $O(\log K)$ time.

### Pattern: Two Heaps for Dynamic Median (LeetCode 295)
- Maintain two heaps:
  1. `small`: Max-heap storing the smaller half of numbers.
  2. `large`: Min-heap storing the larger half of numbers.
- Invariant: `len(small) == len(large)` or `len(small) == len(large) + 1`.
- Every element in `small` $\le$ every element in `large`.
- Finding median takes $O(1)$ time; insertion takes $O(\log N)$ time.

### Pattern: Top-K Frequent Elements / K Closest
- Keep a min-heap of size $K$.
- For each new element, push into heap; if size exceeds $K$, pop the smallest.
- Overall time complexity: $O(N \log K)$ instead of $O(N \log N)$ sorting.

---

## 5. Trie (Prefix Tree)
Efficient for dictionary words, prefix search, and bitwise XOR problems.
- Search / Insert time: $O(L)$ where $L$ is word length.
```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        curr = self.root
        for ch in word:
            if ch not in curr.children:
                curr.children[ch] = TrieNode()
            curr = curr.children[ch]
        curr.is_end = True

    def startsWith(self, prefix: str) -> bool:
        curr = self.root
        for ch in prefix:
            if ch not in curr.children:
                return False
            curr = curr.children[ch]
        return True
```
