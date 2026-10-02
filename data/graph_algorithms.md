# Graph Algorithms — Traversal, Shortest Paths & Trees

## 1. Graph Representations
- **Adjacency List**: `graph = collections.defaultdict(list)`. Space: $O(V + E)$. Best for sparse graphs ($E \ll V^2$).
- **Adjacency Matrix**: `matrix[u][v] = weight`. Space: $O(V^2)$. Best for dense graphs or checking if edge $(u, v)$ exists in $O(1)$.

---

## 2. BFS vs DFS Decision Matrix

| Problem Category | Recommended Technique | Why? |
|---|---|---|
| **Shortest path in unweighted graph** | **BFS** | BFS explores level-by-level; the first time a target is reached, that path has the minimum number of edges. |
| **All paths / Backtracking** | **DFS** | Explores one branch completely, easily rolls back state on return. |
| **Cycle detection (undirected)** | **DFS or DSU** | Detects back-edges to already visited non-parent nodes. |
| **Cycle detection (directed)** | **DFS (3-colors) or Kahn's BFS** | 3-color DFS: 0=White (unvisited), 1=Gray (in current recursion stack), 2=Black (fully explored). A back-edge to a Gray node indicates a directed cycle. |
| **Connected components / Island counting**| **DFS or BFS** | Both visit every node in a component in $O(V + E)$ time. |
| **Topological Sort** | **Kahn's BFS or DFS Post-Order** | Orders vertices in a DAG such that for every directed edge $u \to v$, $u$ comes before $v$. |

---

## 3. Shortest Path Algorithms

### A. Dijkstra's Algorithm (Single Source, Non-negative Weights)
- **Data Structure**: Min-Heap (Priority Queue).
- **Time Complexity**: $O((V + E) \log V)$ with binary heap.
- **Limitation**: Fails or loops indefinitely on negative weight edges.
- **Python Template**:
  ```python
  import heapq

  def dijkstra(graph, start, n):
      dist = {i: float('inf') for i in range(n)}
      dist[start] = 0
      pq = [(0, start)]  # (current_distance, node)

      while pq:
          d, u = heapq.heappop(pq)
          if d > dist[u]:
              continue  # Stale entry

          for v, weight in graph[u]:
              if dist[u] + weight < dist[v]:
                  dist[v] = dist[u] + weight
                  heapq.heappush(pq, (dist[v], v))
      return dist
  ```

### B. Bellman-Ford & SPFA (Handles Negative Weights)
- Relaxes all $E$ edges $V - 1$ times.
- If an edge can still be relaxed on the $V$-th iteration, a **negative weight cycle** exists.
- Time Complexity: $O(V \times E)$.

### C. Floyd-Warshall (All-Pairs Shortest Path)
- Dynamic programming on intermediate vertices $k$:
  `dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])`
- Time Complexity: $O(V^3)$. Best for small graphs ($V \le 400$).

---

## 4. Topological Sorting (DAGs only)

### Kahn's Algorithm (Indegree + BFS)
1. Calculate the in-degree (number of incoming edges) for every vertex.
2. Push all vertices with in-degree `0` into a queue.
3. Pop from queue, add to topological order, and decrement in-degrees of all neighbors.
4. If a neighbor's in-degree drops to `0`, push it to the queue.
5. If the resulting topological order contains fewer than $V$ nodes, the graph has a **cycle**.

---

## 5. Disjoint Set Union (DSU / Union-Find)
- Used for dynamic connectivity, Kruskal's MST, and cycle detection in undirected graphs.
- **Optimizations**: Path Compression + Union by Rank/Size.
- **Amortized Time**: Almost $O(1)$ per operation ($O(\alpha(N))$ Inverse Ackermann function).
- **Python Template**:
  ```python
  class DSU:
      def __init__(self, n):
          self.parent = list(range(n))
          self.rank = [1] * n

      def find(self, i):
          if self.parent[i] != i:
              self.parent[i] = self.find(self.parent[i])  # Path compression
          return self.parent[i]

      def union(self, i, j):
          root_i, root_j = self.find(i), self.find(j)
          if root_i == root_j:
              return False  # Already in same set (cycle detected)
          if self.rank[root_i] < self.rank[root_j]:
              root_i, root_j = root_j, root_i
          self.parent[root_j] = root_i
          if self.rank[root_i] == self.rank[root_j]:
              self.rank[root_i] += 1
          return True
  ```

---

## 6. Minimum Spanning Tree (MST)
- **Kruskal's Algorithm**: Sort all edges by weight ascending; greedily add edges using DSU if they don't form a cycle. Time: $O(E \log E)$.
- **Prim's Algorithm**: Grow a connected component using a min-heap priority queue starting from any node. Time: $O((V + E) \log V)$.
