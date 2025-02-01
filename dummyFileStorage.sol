// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract FileStorage {
    struct File {
        uint256 id;
        string name;
        string category;
        string fileHash;
        address uploadedBy;
        uint256 timestamp;
        bool approved;
        uint256 version;
    }

    File[] public files;
    mapping(address => uint256[]) public userFiles;
    uint256 public filesCount;

    event FileUploaded(uint256 fileId, string name, string category, address indexed uploader, uint256 version);
    event FileApproved(uint256 fileId, address indexed approver);

    // Upload or edit a file
    function uploadFile(string memory name, string memory category, string memory fileHash) public {
        uint256 fileId = files.length;
        uint256 newVersion = 1; // For new files, version starts at 1

        // If the file exists, increment the version number
        for (uint256 i = 0; i < files.length; i++) {
            if (keccak256(abi.encodePacked(files[i].name)) == keccak256(abi.encodePacked(name)) && keccak256(abi.encodePacked(files[i].category)) == keccak256(abi.encodePacked(category))) {
                newVersion = files[i].version + 1;
                break;
            }
        }

        files.push(File(fileId, name, category, fileHash, msg.sender, block.timestamp, false, newVersion));
        userFiles[msg.sender].push(fileId);
        filesCount++;

        emit FileUploaded(fileId, name, category, msg.sender, newVersion);
    }

    // Approve a file
    function approveFile(uint256 fileId) public {
        require(fileId < files.length, "Invalid file ID");
        files[fileId].approved = True;
        emit FileApproved(fileId, msg.sender);
    }

    // Get files uploaded by a user
    function getUserFiles(address user) public view returns (uint256[] memory) {
        return userFiles[user];
    }

    // Get file details
    function getFile(uint256 fileId) public view returns (File memory) {
        require(fileId < files.length, "Invalid file ID");
        return files[fileId];
    }
}
