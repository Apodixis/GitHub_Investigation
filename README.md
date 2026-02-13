# **GitHub Investigation**
This project is a work in progress.
__________________________________________________________________

##### <u>Planned Task(s)</u>
**I have begun the process of generalizing sendRequest functions by:**
<ul>Passing the `variables` dict as an argument instead of declaring in the function</ul>

**I will be continuing this by:**
<ul>Moving cleaning, normalization, and other transformations out of the sendRequests functions</ul>
<ul>Consolidating the simpler sendRequest functions in organizationRequests.py and in userRequests.py into a single file that will be named "sendRequests.py"
__________________________________________________________________

## <u>Search Modes</u>

### **User Search**
#### Option 1: Exact Match
Retrieves information on the input user, their followers, the users they follow, repositories starred, and stargazers of owned repositories.

#### Option 2: Partial Match
Retrieves information on users whose name includes the input substring.

#### Option 3: Author Search <span style="color:#FFA500;">*(Planned, development not yet started)*</span>
Retrieves a list of unique combinations of {login: {fullname, email}} *(type: Dict[Set])*

__________________________________________________________________

### **Organization Search**
#### Option 1: Full Info
Retrieves information on the input organization(s), org members, and org repositories.

#### Option 2: Member Intersection
Retrieves information on the members of the input organization(s) and returns a list of users and their information that exceed the threshold number of organizations they are a member of: *Currently calculated with `math.ceil(1/3) + 1`*

__________________________________________________________________

### **Repository Search** <span style="color:#FFA500;">*(Planned, development not yet started)*</span>
#### Option 1: Full Info
Retrieves information on the input repository, stargazers, network of forks, and contributor information of all repositories in network

#### Options 2: Similar Repositories
Retrieves a list of repositories that share a large overlap in filepaths or have large overlaps in file content for common filenames/filetypes of interest

__________________________________________________________________

### **Email Search** <span style="color:#FFA500;">*(Planned, development not yet started)*</span>
Retrieves information for all commits pushed by a specific email address (or aliased email address) to identify relationships