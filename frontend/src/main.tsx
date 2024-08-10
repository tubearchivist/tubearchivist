import * as React from 'react';
import * as ReactDOM from 'react-dom/client';
import { createBrowserRouter, redirect, RouterProvider } from 'react-router-dom';
import Routes from './configuration/routes/RouteList';
import './style.css';
import Base from './pages/Base';
import About from './pages/About';
import Channels from './pages/Channels';
import ErrorPage from './pages/ErrorPage';
import Home from './pages/Home';
import Logout from './pages/Logout';
import Playlist from './pages/Playlist';
import Playlists from './pages/Playlists';
import Search from './pages/Search';
import SettingsDashboard from './pages/SettingsDashboard';
import Video from './pages/Video';
import Login from './pages/Login';
import SettingsActions from './pages/SettingsActions';
import SettingsApplication from './pages/SettingsApplication';
import SettingsScheduling from './pages/SettingsScheduling';
import SettingsUser from './pages/SettingsUser';
import loadUserMeConfig from './api/loader/loadUserConfig';
import loadAuth from './api/loader/loadAuth';
import ChannelBase from './pages/ChannelBase';
import ChannelVideo from './pages/ChannelVideo';
import ChannelPlaylist from './pages/ChannelPlaylist';
import ChannelAbout from './pages/ChannelAbout';
import ChannelStream from './pages/ChannelStream';
import Download from './pages/Download';
import ChannelShorts from './pages/ChannelShorts';

const router = createBrowserRouter(
  [
    {
      path: Routes.Home,
      loader: async () => {
        console.log('------------ after reload');

        const auth = await loadAuth();
        if (auth.status === 403) {
          return redirect(Routes.Login);
        }

        const authData = await auth.json();

        const userConfig = await loadUserMeConfig();

        return { userConfig, auth: authData };
      },
      element: <Base />,
      errorElement: <ErrorPage />,
      children: [
        {
          index: true,
          element: <Home />,
          loader: async () => {
            const authResponse = await loadAuth();
            if (authResponse.status === 403) {
              return redirect(Routes.Login);
            }

            const userConfig = await loadUserMeConfig();

            return { userConfig };
          },
        },
        {
          path: Routes.Video(':videoId'),
          element: <Video />,
          loader: async () => {
            const authResponse = await loadAuth();
            if (authResponse.status === 403) {
              return redirect(Routes.Login);
            }

            return {};
          },
        },
        {
          path: Routes.Channels,
          element: <Channels />,
          loader: async () => {
            const authResponse = await loadAuth();
            if (authResponse.status === 403) {
              return redirect(Routes.Login);
            }

            const userConfig = await loadUserMeConfig();

            return { userConfig };
          },
        },
        {
          path: Routes.Channel(':channelId'),
          element: <ChannelBase />,
          loader: async () => {
            const authResponse = await loadAuth();
            if (authResponse.status === 403) {
              return redirect(Routes.Login);
            }

            return {};
          },
          children: [
            {
              index: true,
              path: Routes.ChannelVideo(':channelId'),
              element: <ChannelVideo />,
              loader: async () => {
                const authResponse = await loadAuth();
                if (authResponse.status === 403) {
                  return redirect(Routes.Login);
                }

                const userConfig = await loadUserMeConfig();

                return { userConfig };
              },
            },
            {
              path: Routes.ChannelStream(':channelId'),
              element: <ChannelStream />,
              loader: async () => {
                const authResponse = await loadAuth();
                if (authResponse.status === 403) {
                  return redirect(Routes.Login);
                }

                return {};
              },
            },
            {
              path: Routes.ChannelShorts(':channelId'),
              element: <ChannelShorts />,
              loader: async () => {
                const authResponse = await loadAuth();
                if (authResponse.status === 403) {
                  return redirect(Routes.Login);
                }

                return {};
              },
            },
            {
              path: Routes.ChannelPlaylist(':channelId'),
              element: <ChannelPlaylist />,
              loader: async () => {
                const authResponse = await loadAuth();
                if (authResponse.status === 403) {
                  return redirect(Routes.Login);
                }

                const userConfig = await loadUserMeConfig();

                return { userConfig };
              },
            },
            {
              path: Routes.ChannelAbout(':channelId'),
              element: <ChannelAbout />,
              loader: async () => {
                const authResponse = await loadAuth();
                if (authResponse.status === 403) {
                  return redirect(Routes.Login);
                }

                return {};
              },
            },
          ],
        },
        {
          path: Routes.Playlists,
          element: <Playlists />,
          loader: async () => {
            const authResponse = await loadAuth();
            if (authResponse.status === 403) {
              return redirect(Routes.Login);
            }

            const userConfig = await loadUserMeConfig();

            return { userConfig };
          },
        },
        {
          path: Routes.Playlist(':playlistId'),
          element: <Playlist />,
          loader: async () => {
            const authResponse = await loadAuth();
            if (authResponse.status === 403) {
              return redirect(Routes.Login);
            }

            const userConfig = await loadUserMeConfig();

            return { userConfig };
          },
        },
        {
          path: Routes.Downloads,
          element: <Download />,
          loader: async () => {
            const authResponse = await loadAuth();
            if (authResponse.status === 403) {
              return redirect(Routes.Login);
            }

            const userConfig = await loadUserMeConfig();

            return { userConfig };
          },
        },
        {
          path: Routes.Search,
          element: <Search />,
          loader: async () => {
            const authResponse = await loadAuth();
            if (authResponse.status === 403) {
              return redirect(Routes.Login);
            }

            const userConfig = await loadUserMeConfig();

            return { userConfig };
          },
        },
        {
          path: Routes.SettingsDashboard,
          element: <SettingsDashboard />,
          loader: async () => {
            const authResponse = await loadAuth();
            if (authResponse.status === 403) {
              return redirect(Routes.Login);
            }

            return {};
          },
        },
        {
          path: Routes.SettingsActions,
          element: <SettingsActions />,
          loader: async () => {
            const authResponse = await loadAuth();
            if (authResponse.status === 403) {
              return redirect(Routes.Login);
            }

            return {};
          },
        },
        {
          path: Routes.SettingsApplication,
          element: <SettingsApplication />,
          loader: async () => {
            const authResponse = await loadAuth();
            if (authResponse.status === 403) {
              return redirect(Routes.Login);
            }

            return {};
          },
        },
        {
          path: Routes.SettingsScheduling,
          element: <SettingsScheduling />,
          loader: async () => {
            const authResponse = await loadAuth();
            if (authResponse.status === 403) {
              return redirect(Routes.Login);
            }

            return {};
          },
        },
        {
          path: Routes.SettingsUser,
          element: <SettingsUser />,
          loader: async () => {
            const auth = await loadAuth();
            if (auth.status === 403) {
              return redirect(Routes.Login);
            }

            const userConfig = await loadUserMeConfig();

            return { userConfig };
          },
        },
        {
          path: Routes.About,
          element: <About />,
        },
      ],
    },
    {
      path: Routes.Login,
      element: <Login />,
      errorElement: <ErrorPage />,
    },
    {
      path: Routes.Logout,
      element: <Logout />,
      errorElement: <ErrorPage />,
    },
  ],
  { basename: import.meta.env.BASE_URL },
);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);
