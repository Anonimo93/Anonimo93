import axios from "axios";
import { fs } from "fs/promises";

export async function updateBotStatus(status) {
    const data = { botStatus: status };
    await fs.writeFile("./status.json", JSON.stringify(data));

    let content = await fs.readFile("./README.md", { encoding: "utf-8" });

    const regex = /https:\/\/img\.shields\.io\/badge\/GitHub%20Action%20Status-([^-\/]*)-brightgreen\?style=flat&logo=githubactions&logoColor=%23ffffff&labelColor=%23181717&color=%232088FF/;
    const updateUrl = content.replace(regex, `https://img.shields.io/badge/GitHub%20Action%20Status-${status}-brightgreen?style=flat&logo=githubactions&logoColor=%23ffffff&labelColor=%23181717&color=%232088FF`);

    await fs.writeFile("./README.md", updateUrl, { encoding: "utf-8" });
}