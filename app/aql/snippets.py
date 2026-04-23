def aql_return_graph(v_alias: str, e_alias: str, p_alias: str) -> str:
    def aql_get_vertex() -> str:
        return f"""
        LET __vertexMap__ = MERGE(
            FOR v IN {p_alias}.vertices
            RETURN {{ [v._id]: v }}
        )"""

    def aql_path() -> str:
        return f"""
        {{
            edges: (
                FOR e IN {p_alias}.edges
                    RETURN MERGE(e, {{
                        vertex_from: __vertexMap__[e._from],
                        vertex_to: __vertexMap__[e._to]
                    }})
            ),
            vertices: {p_alias}.vertices,
            weights: {p_alias}.weights
        }}
        """

    return f"""
    {aql_get_vertex()}
    RETURN {{
        vertex: {v_alias},
        edge: MERGE({e_alias}, {{
            vertex_from: __vertexMap__[{e_alias}._from],
            vertex_to: __vertexMap__[{e_alias}._to]
        }}),
        path: {aql_path()}
    }}
    """


def aql_return_edge(alias: str) -> str:
    return f"""
    RETURN MERGE({alias}, {{
        vertex_from: DOCUMENT({alias}._from),
        vertex_to: DOCUMENT({alias}._to)
    }})
    """
