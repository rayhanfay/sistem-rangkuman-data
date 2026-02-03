import { onIdTokenChanged, signOut, signInWithEmailAndPassword } from "firebase/auth";
import { auth } from '../utils/firebase';


class AuthService {
    constructor() {
        this.token = null;
    }

    setToken(token) {
        this.token = token;
    }

    getToken() {
        return this.token;
    }


    async login(email, password) {
        return signInWithEmailAndPassword(auth, email, password);
    }

    logout() {
        this.token = null;
        return signOut(auth);
    }
}

const authService = new AuthService();
export default authService;