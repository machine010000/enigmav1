from app.knowledge.graph import KnowledgeGraphService, KnowledgeService, NodeType, RelationType


def test_product_graph_provides_structured_sections():
    service = KnowledgeService()

    product = service.add_product(
        node_id="product:nike_air_max_270",
        name="Nike Air Max 270",
        properties={"brand": "Nike"},
    )
    category = service.add_node(
        node_id="category:shoes",
        node_type=NodeType.CATEGORY,
        name="Shoes",
    )
    feature = service.add_node(
        node_id="feature:running",
        node_type=NodeType.FEATURE,
        name="Running",
    )
    audience = service.add_node(
        node_id="audience:men",
        node_type=NodeType.AUDIENCE,
        name="Men",
    )
    keyword = service.add_node(
        node_id="keyword:running_shoes",
        node_type=NodeType.KEYWORD,
        name="running shoes",
    )

    service.add_relation(product.id, category.id, RelationType.HAS_CATEGORY)
    service.add_relation(product.id, feature.id, RelationType.HAS_FEATURE)
    service.add_relation(product.id, audience.id, RelationType.TARGETS)
    service.add_relation(product.id, keyword.id, RelationType.HAS_KEYWORD)

    product_graph = service.get_product_graph(product.id)

    assert product_graph["product_name"] == "Nike Air Max 270"
    assert any(item["node_id"] == category.id for item in product_graph["sections"]["Category"])
    assert any(item["node_id"] == feature.id for item in product_graph["sections"]["Features"])
    assert any(item["node_id"] == audience.id for item in product_graph["sections"]["Audience"])
    assert any(item["node_id"] == keyword.id for item in product_graph["sections"]["Keywords"])


def test_typed_nodes_and_weighted_relationships_via_service():
    service = KnowledgeService()

    product = service.add_product(
        node_id="product:nike_air_max_270",
        name="Nike Air Max 270",
        properties={"brand": "Nike"},
    )
    problem = service.add_node(
        node_id="problem:foot_pain",
        node_type=NodeType.PROBLEM,
        name="Foot pain",
        properties={"category": "comfort"},
    )

    edge = service.add_relation(
        source_id=product.id,
        target_id=problem.id,
        relation_type=RelationType.SOLVES,
        weight=0.93,
        source="ProductResearchWorker",
        confidence=0.94,
    )

    assert product.type == NodeType.PRODUCT
    assert problem.type == NodeType.PROBLEM
    assert edge.weight == 0.93
    assert edge.source == "ProductResearchWorker"
    assert edge.confidence == 0.94

    neighbors = service.get_neighbors(product.id)
    assert any(neighbor["node_id"] == problem.id for neighbor in neighbors)

    edges = service.get_edges(product.id)
    assert any(edge.relation_type == RelationType.SOLVES for edge in edges)


def test_legacy_graph_service_still_supports_string_based_api():
    graph = KnowledgeGraphService()

    product = graph.create_node("Product", node_id="product:1", properties={"name": "Acme App"})
    audience = graph.create_node("Audience", node_id="audience:1", properties={"name": "SaaS founders"})

    graph.create_edge("product:1", "audience:1", "targets", properties={"weight": 0.9})
    graph.create_edge("product:1", "audience:1", "serves", properties={"source": "manual"})

    neighbors = graph.get_neighbors("product:1")
    assert any(neighbor["node_id"] == "audience:1" for neighbor in neighbors)

    edges = graph.get_edges("product:1")
    assert any(edge["relation"] == "targets" for edge in edges)
    assert any(edge["relation"] == "serves" for edge in edges)

    assert product["node_type"] == "Product"
    assert audience["node_type"] == "Audience"
