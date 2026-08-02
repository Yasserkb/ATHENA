from athena.indexing.common import content_hash
from athena.indexing.parsers.java import JavaParser

SOURCE = """package com.acme;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class OrderController {
    private final OrderService orderService;

    @GetMapping("/orders")
    public String list() {
        return orderService.list();
    }
}
"""


def test_java_parser_extracts_spring_structure() -> None:
    result = JavaParser().analyze("OrderController.java", SOURCE, content_hash(SOURCE))
    nodes = {node.qualified_name: node for node in result.nodes}
    relations = {edge.relation for edge in result.edges}
    assert "com.acme.OrderController" in nodes
    assert nodes["com.acme.OrderController"].metadata["layer"] == "controller"
    assert "EXPOSES_ENDPOINT" in relations
    assert "GET /api/orders" in nodes
    assert "DEPENDS_ON" in relations
    assert "CALLS" in relations
