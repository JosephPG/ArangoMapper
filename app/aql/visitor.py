class BindVarVisitor:
    def __init__(self):
        self.counter: int = 0
        self.bind_vars: dict = {}

    def add(self, value: any):
        key = self._build_key()
        self.bind_vars[key] = value

    def _build_key(self):
        pass


# https://refactoring.guru/design-patterns/visitor
# # Los "Elementos" de tu AQL
# class For:
#     def accept(self, visitor):
#         return visitor.visit_for(self)

# class Let:
#     def accept(self, visitor):
#         return visitor.visit_let(self)

# # El "Visitante" (Tu orquestador de lógica)
# class AQLGeneratorVisitor:
#     def __init__(self, bv_manager):
#         self.bv = bv_manager

#     def visit_for(self, element):
#         # Aquí defines cómo se ve un FOR en Arango
#         return f"FOR {element.alias} IN {element.collection_name}"

#     def visit_let(self, element):
#         # Aquí defines cómo se ve un LET
#         var_name = self.bv.add(element.value)
#         return f"LET {element.variable} = {var_name}"
