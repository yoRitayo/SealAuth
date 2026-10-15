import { createBrowserRouter } from "react-router-dom";
import { Root } from "./Root";

export const Router = createBrowserRouter([
    {
        path: '/',
        Component: Root,
    },

    {
        path: '/entrar',
        Component: Root,
    },

    {
        path: '/reset-senha',
        Component: Root, 
    },

    {
        path: '/registrar',
        Component: Root,
    },

    {
        path: '/inicio',
        Component: Root,
    }
])