"""Module to store information about branches in a ROOT TTree."""
class BranchInfo:
    """Store information about a single branch."""
    
    def __init__(self, name: str, typename: str, title: str):
        """
        Initialize branch information.
        
        Args:
            name: Branch name
            typename: Branch type name
            title: Branch title/description
        """
        self.name = name
        self.typename = typename
        self.title = title
    
    def __repr__(self) -> str:
        return f"BranchInfo(name='{self.name}', type='{self.typename}', title='{self.title}')"
    
    def __str__(self) -> str:
        return f"{self.name:50s} {self.typename:20s}"

