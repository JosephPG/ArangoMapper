from arangomapper.aql.schemas import ForGraphData


def aql_return_graph(v_alias: str, e_alias: str, p_alias: str) -> str:
    def aql_get_vertex() -> str:
        return f"""
        LET __vertexMap__ = MERGE(
            FOR _inter_{v_alias}_ IN {p_alias}.vertices
            RETURN {{ [_inter_{v_alias}_._id]: _inter_{v_alias}_ }}
        )"""

    def aql_path() -> str:
        return f"""
        {{
            edges: (
                FOR _inner_{e_alias}_ IN {p_alias}.edges
                    RETURN MERGE(_inner_{e_alias}_, {{
                        vertex_from: __vertexMap__[_inner_{e_alias}_._from],
                        vertex_to: __vertexMap__[_inner_{e_alias}_._to]
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


def aql_return_graph_edge(v_alias: str, e_alias: str, p_alias: str) -> str:
    def aql_get_vertex() -> str:
        return f"""
        LET __vertexMap__ = MERGE(
            FOR _inner_{v_alias}_ IN {p_alias}.vertices
            RETURN {{ [_inner_{v_alias}_._id]: _inner_{v_alias}_ }}
        )"""

    return (
        f"""
    MERGE({e_alias}, {{
        vertex_from: __vertexMap__[{e_alias}._from],
        vertex_to: __vertexMap__[{e_alias}._to]
    }})
    """,
        aql_get_vertex(),
    )


def aql_return_edge(alias: str) -> str:
    return f"""
    RETURN MERGE({alias}, {{
        vertex_from: DOCUMENT({alias}._from),
        vertex_to: DOCUMENT({alias}._to)
    }})
    """


def aql_return(content: str) -> str:
    return f" RETURN {content} "


def aql_sort(content: str) -> str:
    return f" SORT {content} "


def aql_let(content: str) -> str:
    return f"LET {content} "


def aql_limit(content: str) -> str:
    return f"LIMIT {content} "


def aql_for(alias: str, collection: str) -> str:
    return f" FOR {alias} in {collection} "


def aql_for_graph(
    graph_data: ForGraphData, d_min: int, d_max: int, direction: str, id: str
) -> str:
    alias: str = f"{graph_data.v_alias}, {graph_data.e_alias}, {graph_data.p_alias}"
    depth: str = f"{d_min}..{d_max}"
    return f" FOR {alias} IN {depth} {direction} '{id}' GRAPH {graph_data.graph_name} "
