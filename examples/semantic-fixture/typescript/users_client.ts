export async function loadUser(userId: string): Promise<unknown> {
  return axios.get(`/users/${userId}`);
}
